# app/api/candidate.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from typing import Optional, List, Literal, Dict, Any
import json

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario, TipoUsuario
from app.services.nvidia import NvidiaServiceError, configured_model, is_configured, json_completion

router = APIRouter()

# =========================
# Modelos de respuesta
# =========================

class VacanteItem(BaseModel):
    id: int
    titulo: str
    descripcion: Optional[str] = None
    requisitos: Optional[str] = None
    ubicacion: Optional[str] = None
    tipo_contrato: Optional[str] = None
    salario_min: Optional[float] = None
    salario_max: Optional[float] = None
    estado: str
    reclutador_id: Optional[int] = None
    total_postulaciones: Optional[int] = 0
    aplicada: bool = False

class PagedVacantesResponse(BaseModel):
    items: List[VacanteItem]
    page: int
    page_size: int
    total: int
    pages: int

class EvalQuestion(BaseModel):
    id: str
    prompt: str
    type: Literal["text","number","boolean","code","case"] = "text"
    weight: int = 10
    rubric: Optional[str] = None
    hint: Optional[str] = None

class EvalTechTest(BaseModel):
    id: str
    title: str
    instructions: str
    expected_outcome: str
    time_limit_min: int = 30
    weight: int = 30
    rubric: Optional[str] = None
    files_allowed: bool = False

class CandidateEvaluation(BaseModel):
    vacante_id: int
    questions: List[EvalQuestion]
    technical_tests: List[EvalTechTest]

class AIEnvelope(BaseModel):
    evaluation: CandidateEvaluation

class PostularResponse(BaseModel):
    ok: bool
    message: str
    vacante_id: int
    ai: AIEnvelope

class AnswerItem(BaseModel):
    id: str
    response: str

class CandidateSubmission(BaseModel):
    answers: List[AnswerItem]

class ItemScore(BaseModel):
    id: str
    title: Optional[str] = None
    type: str
    weight: int
    score: int
    comments: str

class EvaluationResult(BaseModel):
    vacante_id: int
    candidato_id: int
    total_max: int
    total_obtained: int
    percentage: float
    recommendation: str
    details: List[ItemScore]
    used_evaluation: Dict[str, Any]

# =========================
# Dependencias
# =========================
def _recommendation(pct: float) -> str:
    """
    Devuelve una recomendación basada en el porcentaje de puntaje.
    """
    if pct >= 85:
        return "Contratar"
    elif pct >= 70:
        return "Considerar"
    elif pct >= 50:
        return "Revisar cuidadosamente"
    else:
        return "No recomendable"


def require_candidate(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if current_user.tipo != TipoUsuario.candidato.value:
        raise HTTPException(status_code=403, detail="Solo candidatos")
    return current_user

# =========================
# Helpers de candidatos / FK
# =========================

def _get_or_create_model_id(db: Session) -> int:
    model_name = "nvidia:" + configured_model() if is_configured() else "heuristic"
    try:
        row = db.execute(text("SELECT id FROM modelos_ia WHERE nombre = :n LIMIT 1"), {"n": model_name}).fetchone()
        if row:
            return int(row[0])
        db.execute(text("INSERT INTO modelos_ia (nombre) VALUES (:n)"), {"n": model_name})
        db.commit()
        return int(db.execute(text("SELECT LAST_INSERT_ID()")).scalar())
    except Exception:
        return 1

def _get_candidato_id(db: Session, current_user: Usuario) -> int:
    try:
        row = db.execute(
            text("SELECT id FROM candidatos WHERE usuario_id = :uid LIMIT 1"),
            {"uid": current_user.id}
        ).fetchone()
        if row: return int(row[0])
    except Exception: pass
    try:
        row = db.execute(
            text("SELECT id FROM candidatos WHERE id_usuario = :uid LIMIT 1"),
            {"uid": current_user.id}
        ).fetchone()
        if row: return int(row[0])
    except Exception: pass
    try:
        row = db.execute(
            text("SELECT id FROM candidatos WHERE correo = :correo LIMIT 1"),
            {"correo": current_user.correo}
        ).fetchone()
        if row: return int(row[0])
    except Exception: pass
    raise HTTPException(
        status_code=400,
        detail="No existe un registro en la tabla 'candidatos' asociado a tu usuario."
    )

# =========================
# IA / Heurística
# =========================

ROLE_KEYWORDS = {
    "dev": ["desarrollador","developer","engineer","ingeniero","programador","backend","frontend","fullstack",
            "node","react","python","java","php","laravel","django","flask","spring","fastapi","express",
            "typescript","javascript","sql","postgres","mysql","docker","aws"],
    "data": ["data","analista de datos","data analyst","bi","power bi","sql","etl","warehouse","bigquery",
             "snowflake","excel","estadística","dashboards","kpi","pandas"],
    "design": ["diseñador","ux","ui","product designer","figma","sketch","design system","accesibilidad","wireframe","prototipo"],
    "sales": ["ventas","account executive","comercial","bdm","negocios","prospectar","pipeline","crm","negociación","cierre"],
    "support": ["soporte","help desk","service desk","incidente","sla","ticket","diagnóstico","troubleshooting"],
    "pm": ["product manager","project manager","scrum","kanban","gestión de proyectos","roadmap","priorización"],
}

def _norm(s: Optional[str]) -> str: return (s or "").lower()
def _detect_role(v: Dict[str, Any]) -> str:
    blob = " ".join([_norm(v.get("titulo")), _norm(v.get("descripcion")), _norm(v.get("requisitos"))])
    for role, kws in ROLE_KEYWORDS.items():
        if any(kw in blob for kw in kws): return role
    return "dev"

WEIGHTS = {"q": 10, "t": 30}
RUBRICS = {
    "soft": "Claridad, estructura, relevancia y ejemplos. 0–10.",
    "code": "Correctitud, legibilidad, manejo de errores, pruebas. 0–30.",
    "sql":  "Uso de SELECT/JOIN/WHERE/índices, eficiencia y justificación. 0–30.",
}

def _heuristic_eval(v: Dict[str, Any], vacante_id: int) -> CandidateEvaluation:
    """Genera evaluación usando las preguntas de la vacante si existen, sino heurística"""
    questions = []
    technical_tests = []

    # Verificar si la vacante tiene JSON con preguntas/prueba técnica
    if v.get("datos"):
        try:
            datos = json.loads(v["datos"])
            for i, q in enumerate(datos.get("preguntas", [])):
                questions.append(EvalQuestion(
                    id=f"q{i+1}", prompt=q, weight=WEIGHTS["q"], rubric=RUBRICS["soft"]
                ))
            if datos.get("prueba_tecnica"):
                pt = datos["prueba_tecnica"]
                technical_tests.append(EvalTechTest(
                    id="t1",
                    title=pt.get("titulo","Prueba técnica"),
                    instructions=pt.get("instrucciones", pt.get("instrucciones","")),
                    expected_outcome=pt.get("criterios",""),
                    weight=WEIGHTS["t"],
                    rubric=RUBRICS["soft"]
                ))
        except Exception:
            pass

    # Fallback heurístico si no hay preguntas
    if not questions:
        role = _detect_role(v)
        titulo = v.get("titulo") or "la posición"
        questions = [
            EvalQuestion(id="q_exp",  prompt=f"Describe un proyecto reciente alineado a {titulo}. ¿Qué lograste y qué aprendiste?", weight=WEIGHTS["q"], rubric=RUBRICS["soft"]),
            EvalQuestion(id="q_reto", prompt="¿Cuál fue tu reto más complejo y cómo lo resolviste (paso a paso)?", weight=WEIGHTS["q"], rubric=RUBRICS["soft"]),
            EvalQuestion(id="q_90",   prompt="Propón una mejora para los primeros 90 días y cómo medirías su éxito.", weight=WEIGHTS["q"], rubric=RUBRICS["soft"]),
        ] 
        # Tests heurísticos
        if role == "dev":
            technical_tests = [
                EvalTechTest(id="t_api", title="Mini API CRUD", instructions="Implementa endpoint CRUD con validaciones y 3 tests. Incluye README.", expected_outcome="API funcional + tests", weight=WEIGHTS["t"], rubric=RUBRICS["code"], files_allowed=True),
                EvalTechTest(id="t_sql", title="Optimización SQL", instructions="Consulta con JOINs optimizada e índices propuestos con justificación.", expected_outcome="Consulta eficiente + índices", weight=WEIGHTS["t"], rubric=RUBRICS["sql"], files_allowed=False),
            ]
        else:
            technical_tests = [
                EvalTechTest(id="t_case1", title="Caso práctico", instructions="Caso breve del rol con pasos y métricas.", expected_outcome="Caso claro + métricas", weight=WEIGHTS["t"], rubric=RUBRICS["soft"]),
            ]

    return CandidateEvaluation(vacante_id=vacante_id, questions=questions, technical_tests=technical_tests)

def _eval_with_nvidia(evaluation: CandidateEvaluation, submission: CandidateSubmission) -> Dict[str, Any]:
    """Evalúa y normaliza la respuesta; el servidor, no el modelo, calcula totales."""
    items = [*evaluation.questions, *evaluation.technical_tests]
    rubric = "\n".join(f"- {item.id}: máximo {item.weight}; {getattr(item, 'rubric', '') or ''}" for item in items)
    answers = "\n".join(f"- {answer.id}: {answer.response}" for answer in submission.answers)
    prompt = f"""Evalúa las respuestas de un candidato. Devuelve exclusivamente un objeto JSON:
{{"results":[{{"id":"identificador","score":numero,"comments":"comentario breve"}}]}}
Incluye exactamente estos criterios y no inventes identificadores:
{rubric}
Respuestas del candidato:
{answers}
Puntúa con imparcialidad, en español. No incluyas total ni porcentaje."""
    data = json_completion(
        [{"role": "system", "content": "Eres un evaluador de selección de personal imparcial. Respondes solo JSON."}, {"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=2000,
    )
    raw_results = data.get("results")
    if not isinstance(raw_results, list):
        raise NvidiaServiceError("La evaluación no contiene resultados válidos.")
    by_id = {str(result.get("id")): result for result in raw_results if isinstance(result, dict)}
    results = []
    for item in items:
        result = by_id.get(item.id)
        if result is None:
            raise NvidiaServiceError("La evaluación está incompleta.")
        try:
            score = int(round(float(result.get("score"))))
        except (TypeError, ValueError) as exc:
            raise NvidiaServiceError("La evaluación contiene un puntaje inválido.") from exc
        results.append({
            "id": item.id, "title": getattr(item, "title", None) or item.id,
            "type": getattr(item, "type", "test"), "weight": item.weight,
            "score": max(0, min(score, item.weight)),
            "comments": str(result.get("comments", "Sin comentarios.")).strip()[:1000],
        })
    total = sum(result["score"] for result in results)
    maximum = sum(item.weight for item in items)
    return {"results": results, "total_score": total, "percentage": round(total * 100 / maximum, 2) if maximum else 0.0}


def _eval_with_heuristic(evaluation: CandidateEvaluation, submission: CandidateSubmission) -> Dict[str, Any]:
    """Respaldo local para no bloquear una postulación si el proveedor de IA falla."""
    answers = {answer.id: answer.response.strip() for answer in submission.answers}
    results = []
    for item in [*evaluation.questions, *evaluation.technical_tests]:
        response = answers.get(item.id, "")
        if len(response) < 20:
            score = max(1, item.weight // 4)
            comment = "Respuesta muy corta; se recomienda ampliar los detalles."
        elif len(response) < 50:
            score = max(1, item.weight // 2)
            comment = "Respuesta aceptable, aunque puede ser más completa."
        else:
            score = item.weight
            comment = "Respuesta completa y detallada."
        results.append({
            "id": item.id,
            "title": getattr(item, "title", None) or item.id,
            "type": getattr(item, "type", "test"),
            "weight": item.weight,
            "score": score,
            "comments": comment,
        })
    total = sum(result["score"] for result in results)
    maximum = sum(item.weight for item in [*evaluation.questions, *evaluation.technical_tests])
    return {"results": results, "total_score": total, "percentage": round(total * 100 / maximum, 2) if maximum else 0.0}

def _generate_eval(v: Dict[str, Any], vacante_id: int) -> CandidateEvaluation:
    # La evaluación inicial sale de los datos persistidos o de una plantilla local.
    # NVIDIA queda reservado para la calificación posterior y no bloquea al candidato.
    return _heuristic_eval(v, vacante_id)


# =========================
# ENDPOINTS
# =========================

@router.get("/vacantes", response_model=PagedVacantesResponse)
async def listar_vacantes(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    q: Optional[str] = Query(None),
    modalidad: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_candidate),
):
    candidato_id = _get_candidato_id(db, current_user)
    where = ["v.estado = 'activa'"]
    params = {}
    if q:
        where.append("(v.titulo LIKE :q OR v.descripcion LIKE :q OR v.requisitos LIKE :q OR v.ubicacion LIKE :q)")
        params["q"] = f"%{q.strip()}%"
    if modalidad:
        where.append("v.modalidad = :mod")
        params["mod"] = modalidad.strip().lower()
    where_sql = " AND ".join(where)
    total = db.execute(text(f"SELECT COUNT(*) c FROM vacantes v WHERE {where_sql}"), params).scalar() or 0
    rows = db.execute(
        text(f"""
            SELECT v.id, v.titulo, v.descripcion, v.requisitos, v.ubicacion,
                   v.modalidad AS tipo_contrato, v.salario_min, v.salario_max, v.estado,
                   v.id_reclutador AS reclutador_id,
                   (SELECT COUNT(*) FROM postulaciones p WHERE p.id_vacante = v.id) AS total_postulaciones,
                   EXISTS(
                       SELECT 1
                       FROM postulaciones p
                       JOIN evaluaciones e ON e.id_postulacion = p.id
                       WHERE p.id_vacante = v.id
                         AND p.id_candidato = :candidate_id
                         AND e.nivel <> 'pendiente'
                   ) AS aplicada
            FROM vacantes v
            WHERE {where_sql}
            ORDER BY v.id DESC
            LIMIT :limit OFFSET :offset
        """),
        {**params, "candidate_id": candidato_id, "limit": page_size, "offset": (page-1)*page_size}
    ).fetchall()
    items = [VacanteItem(**dict(r._mapping)) for r in rows]
    pages = max(1, (total + page_size - 1) // page_size)
    return PagedVacantesResponse(items=items, page=page, page_size=page_size, total=total, pages=pages)

@router.post("/vacantes/{vacante_id}/evaluar", response_model=EvaluationResult)
async def evaluar(
    vacante_id: int,
    submission: CandidateSubmission,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_candidate),
):
    # Obtener ID del candidato
    candidato_id = _get_candidato_id(db, current_user)

    # Verificar postulación
    ex = db.execute(
        text("SELECT 1 FROM postulaciones WHERE id_vacante = :v AND id_candidato = :c LIMIT 1"),
        {"v": vacante_id, "c": candidato_id}
    ).fetchone()
    if not ex:
        raise HTTPException(status_code=400, detail="Debes postularte antes de enviar la evaluación")

    # Obtener vacante
    vrow = db.execute(
        text("""SELECT id, titulo, descripcion, requisitos, ubicacion, modalidad AS tipo_contrato,
                       salario_min, salario_max, id_reclutador, datos
                FROM vacantes WHERE id = :id AND estado = 'activa'"""),
        {"id": vacante_id}
    ).fetchone()
    if not vrow:
        raise HTTPException(status_code=404, detail="Vacante no encontrada")
    vacante = dict(vrow._mapping)

    # Generar evaluación con IA
    evaluation = _generate_eval(vacante, vacante_id)

    try:
        ai_scores = _eval_with_nvidia(evaluation, submission)
    except NvidiaServiceError:
        # El candidato puede terminar su postulación aun cuando NVIDIA no esté disponible.
        ai_scores = _eval_with_heuristic(evaluation, submission)
    details = [ItemScore(**result) for result in ai_scores["results"]]
    total_obtained = ai_scores["total_score"]
    pct = ai_scores["percentage"]

    # Obtener ID de la postulación
    post_row = db.execute(
        text("SELECT id FROM postulaciones WHERE id_vacante = :v AND id_candidato = :c ORDER BY fecha_postulacion DESC LIMIT 1"),
        {"v": vacante_id, "c": candidato_id}
    ).fetchone()
    id_postulacion = int(post_row[0])

    # Obtener ID del modelo IA
    id_modelo = _get_or_create_model_id(db)

    # Determinar nivel según porcentaje
    nivel = "alto" if pct >= 85.0 else ("medio" if pct >= 70.0 else "bajo")

    # Construir objeto completo de evaluación
    evaluation_data = {
        "total_max": sum([q.weight for q in evaluation.questions] + [t.weight for t in evaluation.technical_tests]),
        "total_obtained": total_obtained,
        "percentage": pct,
        "recommendation": _recommendation(pct),
        "details": [d.dict() for d in details],
        "used_evaluation": {
            "questions": [q.dict() for q in evaluation.questions],
            "technical_tests": [t.dict() for t in evaluation.technical_tests]
        }
    }

    # Guardar evaluación en DB
    db.execute(
        text("""INSERT INTO evaluaciones
                (id_postulacion, id_modelo, puntaje, observacion, nivel, datos, fecha_evaluacion)
                VALUES (:p, :m, :punt, :obs, :niv, :datos, NOW())"""),
        {
            "p": id_postulacion,
            "m": id_modelo,
            "punt": int(round(pct)),
            "obs": f"Recomendación: {evaluation_data['recommendation']}. Puntaje: {pct}%",
            "niv": nivel,
            "datos": json.dumps(evaluation_data, ensure_ascii=False)
        }
    )

    # Actualizar estado de postulación
    db.execute(
        text("UPDATE postulaciones SET estado = 'evaluado' WHERE id = :p"),
        {"p": id_postulacion}
    )
    db.commit()

    # Devolver resultado
    return EvaluationResult(
        vacante_id=vacante_id,
        candidato_id=candidato_id,
        total_max=evaluation_data["total_max"],
        total_obtained=total_obtained,
        percentage=pct,
        recommendation=evaluation_data["recommendation"],
        details=details,
        used_evaluation=evaluation_data["used_evaluation"]
    )

@router.get("/mis-postulaciones")
async def mis_postulaciones(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_candidate),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    candidato_id = _get_candidato_id(db, current_user)
    rows = db.execute(
        text("""SELECT p.id, p.id_vacante, v.titulo, p.estado, p.fecha_postulacion
                FROM postulaciones p
                JOIN vacantes v ON v.id = p.id_vacante
                WHERE p.id_candidato = :c
                ORDER BY p.fecha_postulacion DESC
                LIMIT :limit OFFSET :offset"""),
        {"c": candidato_id, "limit": page_size, "offset": (page-1)*page_size}
    ).fetchall()
    return {"ok": True, "data": [dict(r._mapping) for r in rows]}

@router.post("/vacantes/{vacante_id}/evaluar", response_model=EvaluationResult)
async def evaluar_postulacion_heuristica(
    vacante_id: int,
    submission: CandidateSubmission,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_candidate),
):
    candidato_id = _get_candidato_id(db, current_user)
    vacante_row = db.execute(text("SELECT * FROM vacantes WHERE id = :id"), {"id": vacante_id}).mappings().first()
    if not vacante_row:
        raise HTTPException(status_code=404, detail="Vacante no encontrada")

    evaluation = _heuristic_eval(vacante_row, vacante_id)
    details: List[ItemScore] = []
    total_max = sum(q.weight for q in evaluation.questions) + sum(t.weight for t in evaluation.technical_tests)
    total_obtained = 0

    # =====================
    # Evaluación de preguntas
    # =====================
    answers_map = {a.id: a.response for a in submission.answers}
    for q in evaluation.questions:
        resp = answers_map.get(q.id,"").strip()
        score = 0
        comments = ""

        # Heurística simple: longitud y presencia de palabras clave
        if len(resp) < 20:
            score = max(1, q.weight // 4)
            comments = "Respuesta muy corta, ampliar con más detalles."
        elif len(resp) < 50:
            score = max(1, q.weight // 2)
            comments = "Respuesta aceptable, pero podría ser más completa."
        else:
            score = q.weight
            comments = "Respuesta completa y detallada."

        total_obtained += score
        details.append(ItemScore(id=q.id, type="question", weight=q.weight, score=score, comments=comments))

    # =====================
    # Evaluación de pruebas técnicas
    # =====================
    for t in evaluation.technical_tests:
        resp = answers_map.get(t.id,"").strip()
        score = 0
        comments = ""

        # Heurística simple: longitud y presencia de palabras clave según título
        key_words = t.title.lower().split()
        found_kw = sum(1 for kw in key_words if kw in resp.lower())
        ratio = found_kw / max(1, len(key_words))

        if len(resp) < 50:
            score = max(1, t.weight // 4)
            comments = "Prueba incompleta, requiere más detalle o implementación."
        elif ratio < 0.5:
            score = max(1, t.weight // 2)
            comments = "Algunos criterios del título no fueron abordados."
        else:
            score = t.weight
            comments = "Prueba técnica completa y adecuada."

        total_obtained += score
        details.append(ItemScore(id=t.id, type="test", weight=t.weight, score=score, comments=comments))

    percentage = round((total_obtained / total_max) * 100, 2) if total_max else 0.0
    recommendation = _recommendation(percentage)
    obs_text = "\n".join([f"{d.id}: {d.comments}" for d in details])

    # Guardado en DB
    db.execute(
        text("""INSERT INTO evaluaciones
                (id_postulacion, id_modelo, puntaje, observacion, nivel, datos, fecha_evaluacion)
                VALUES (:p, :m, :punt, :obs, :niv, :datos, NOW())"""),
        {
            "p": candidato_id,
            "m": _get_or_create_model_id(db),
            "punt": total_obtained,
            "obs": obs_text,
            "niv": recommendation,
            "datos": json.dumps({
                "details": [d.dict() for d in details],
                "submission": submission.dict(),
                "heuristic": True
            }, ensure_ascii=False)
        }
    )
    db.commit()

    return EvaluationResult(
        vacante_id=vacante_id,
        candidato_id=candidato_id,
        total_max=total_max,
        total_obtained=total_obtained,
        percentage=percentage,
        recommendation=recommendation,
        details=details,
        used_evaluation={
            "questions": [q.dict() for q in evaluation.questions],
            "technical_tests": [t.dict() for t in evaluation.technical_tests],
            "heuristic": True
        }
    )

@router.post("/vacantes/{vacante_id}/postular", response_model=PostularResponse)
async def postular_vacante(
    vacante_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_candidate)
):
    candidato_id = _get_candidato_id(db, current_user)

    # Verificar si ya existe postulación
    existing = db.execute(
        text("""SELECT p.id, p.estado,
                       EXISTS(
                           SELECT 1 FROM evaluaciones e
                           WHERE e.id_postulacion = p.id AND e.nivel <> 'pendiente'
                       ) AS evaluacion_enviada
                FROM postulaciones p
                WHERE p.id_vacante = :v AND p.id_candidato = :c
                LIMIT 1"""),
        {"v": vacante_id, "c": candidato_id}
    ).fetchone()

    # Obtener datos de la vacante
    vrow = db.execute(
        text("""SELECT id, titulo, descripcion, requisitos, ubicacion,
                       modalidad AS tipo_contrato, salario_min, salario_max,
                       id_reclutador, datos
                FROM vacantes WHERE id = :id AND estado = 'activa'"""),
        {"id": vacante_id}
    ).fetchone()
    if not vrow:
        raise HTTPException(status_code=404, detail="Vacante no encontrada")
    vacante = dict(vrow._mapping)

    # 1️⃣ Generar preguntas/tests con IA
    evaluation = _generate_eval(vacante, vacante_id)

    # Una evaluación pendiente se puede retomar. Solo se considera aplicada
    # cuando el candidato la envía y su estado pasa a "evaluado".
    if existing:
        if existing.evaluacion_enviada:
            raise HTTPException(status_code=409, detail="Ya aplicaste a esta vacante.")
        return PostularResponse(
            ok=True,
            message="Tienes una evaluación pendiente por completar.",
            vacante_id=vacante_id,
            ai=AIEnvelope(evaluation=evaluation),
        )

    try:
        result = db.execute(
            text("INSERT INTO postulaciones (id_vacante, id_candidato, fecha_postulacion, estado) VALUES (:v, :c, NOW(), 'pendiente')"),
            {"v": vacante_id, "c": candidato_id}
        )
        postulacion_id = result.lastrowid

    # 2️⃣ Guardar esas preguntas en la tabla evaluaciones o en una tabla auxiliar
        db.execute(
            text("""INSERT INTO evaluaciones (id_postulacion, id_modelo, puntaje, observacion, nivel, datos, fecha_evaluacion)
                    VALUES (:p, :m, 0, 'Preguntas generadas con IA', 'pendiente', :datos, NOW())"""),
            {
                "p": postulacion_id,
                "m": _get_or_create_model_id(db),
                "datos": json.dumps({
                    "questions": [q.dict() for q in evaluation.questions],
                    "technical_tests": [t.dict() for t in evaluation.technical_tests]
                }, ensure_ascii=False)
            }
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya aplicaste a esta vacante.") from exc

    # 3️⃣ Retornar respuesta
    ai_env = AIEnvelope(evaluation=evaluation)
    return PostularResponse(
        ok=True,
        message="Postulación realizada y preguntas guardadas en DB.",
        vacante_id=vacante_id,
        ai=ai_env
    )
