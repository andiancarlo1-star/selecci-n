from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os, json, re
from io import BytesIO
from datetime import datetime
from typing import Literal
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario, TipoUsuario
from app.models.reclutador import Reclutador
from app.models.candidato import Candidato

router = APIRouter()

# ==============================
def _instant_interview(data: "VacanteCreate") -> dict:
    """Entrevista inicial local: evita bloquear la publicación por un proveedor externo."""
    title = data.titulo.strip()
    requirements = (data.requisitos or "los requisitos descritos para la vacante").strip()
    return {
        "preguntas": [
            f"Describe una experiencia relevante para el puesto de {title}.",
            f"¿Cómo aplicarías {requirements} en los primeros 90 días?",
            "Cuéntanos un reto profesional, cómo lo resolviste y cómo mediste el resultado.",
        ],
        "prueba_tecnica": {
            "titulo": f"Caso práctico de {title}",
            "instrucciones": f"Propón una solución breve para una situación real del puesto, considerando: {requirements}.",
            "criterios": "Claridad, relevancia, razonamiento, viabilidad y métricas de éxito.",
        },
    }

# ==============================
# Modelos Pydantic
# ==============================
class VacanteCreate(BaseModel):
    titulo: str
    descripcion: str
    requisitos: Optional[str] = None
    ubicacion: Optional[str] = None
    tipo_contrato: Optional[str] = "presencial"
    salario_min: Optional[float] = None
    salario_max: Optional[float] = None

class EstadoPostulacion(BaseModel):
    estado: Literal["aceptado", "rechazado"]

# ==============================
# Dependencia de reclutador
# ==============================
def require_recruiter(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if current_user.tipo not in (TipoUsuario.reclutador.value, TipoUsuario.admin.value):
        raise HTTPException(status_code=403, detail="Solo reclutador puede hacer esta acción")
    return current_user

# ==============================
# Función auxiliar para servir CV
# ==============================
def _serve_cv(candidato: Candidato) -> FileResponse:
    if not candidato or not candidato.cv_url:
        raise HTTPException(status_code=404, detail="CV no encontrado")

    path = candidato.cv_url
    if not path.startswith("uploads/"):
        path = f"uploads/{path.lstrip('/')}"

    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Archivo CV no encontrado en servidor")

    filename = os.path.basename(path) or f"cv_{candidato.id}.pdf"
    return FileResponse(path, filename=filename, media_type="application/pdf")

# ==============================
# CREAR VACANTE
# ==============================
@router.post("/vacantes")
async def crear_vacante(
    data: VacanteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_recruiter)
):
    reclutador = db.query(Reclutador).filter(Reclutador.id_usuario == current_user.id).first()
    if not reclutador:
        raise HTTPException(status_code=400, detail="Reclutador no encontrado")

    entrevista_json = _instant_interview(data)

    db.execute(
        text("""
            INSERT INTO vacantes 
            (titulo, descripcion, requisitos, ubicacion, modalidad, salario_min, salario_max, estado, id_reclutador, fecha_publicacion, entrevista, datos)
            VALUES 
            (:titulo, :descripcion, :requisitos, :ubicacion, :modalidad, :salario_min, :salario_max, 'activa', :id_reclutador, NOW(), :entrevista, :datos)
        """),
        {
            "titulo": data.titulo,
            "descripcion": data.descripcion,
            "requisitos": data.requisitos,
            "ubicacion": data.ubicacion,
            "modalidad": data.tipo_contrato,
            "salario_min": data.salario_min,
            "salario_max": data.salario_max,
            "id_reclutador": reclutador.id,
            "entrevista": json.dumps(entrevista_json, ensure_ascii=False),
            "datos": json.dumps(entrevista_json, ensure_ascii=False),
        }
    )
    db.commit()
    return {"ok": True, "message": "Vacante publicada inmediatamente", "entrevista": entrevista_json}

# ==============================
# LISTAR VACANTES
# ==============================
@router.get("/vacantes")
async def listar_vacantes(db: Session = Depends(get_db), current_user: Usuario = Depends(require_recruiter)):
    reclutador = db.query(Reclutador).filter(Reclutador.id_usuario == current_user.id).first()
    if not reclutador:
        raise HTTPException(status_code=404, detail="Reclutador no encontrado")
    vacantes = db.execute(
        text("SELECT * FROM vacantes WHERE id_reclutador = :rid"),
        {"rid": reclutador.id}
    ).fetchall()
    return {"ok": True, "vacantes": [dict(v._mapping) for v in vacantes]}

# ==============================
# CERRAR / ABRIR VACANTE
# ==============================
@router.post("/vacantes/{vacante_id}/cerrar")
async def cerrar_vacante(vacante_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(require_recruiter)):
    reclutador = db.query(Reclutador).filter(Reclutador.id_usuario == current_user.id).first()
    if not reclutador:
        raise HTTPException(status_code=400, detail="Reclutador no encontrado")
    result = db.execute(
        text("UPDATE vacantes SET estado='cerrada' WHERE id=:vid AND id_reclutador=:rid"),
        {"vid": vacante_id, "rid": reclutador.id}
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Vacante no encontrada o no autorizada")
    db.commit()
    return {"ok": True, "message": "Vacante cerrada con éxito"}

@router.post("/vacantes/{vacante_id}/abrir")
async def abrir_vacante(vacante_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(require_recruiter)):
    reclutador = db.query(Reclutador).filter(Reclutador.id_usuario == current_user.id).first()
    if not reclutador:
        raise HTTPException(status_code=400, detail="Reclutador no encontrado")
    result = db.execute(
        text("UPDATE vacantes SET estado='activa' WHERE id=:vid AND id_reclutador=:rid"),
        {"vid": vacante_id, "rid": reclutador.id}
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Vacante no encontrada o no autorizada")
    db.commit()
    return {"ok": True, "message": "Vacante reabierta con éxito"}

# ==============================
# POSTULACIONES
# ==============================
def _fetch_postulaciones_recruiter(db: Session, reclutador_id: int, vacante_id: Optional[int] = None) -> List[Dict[str, Any]]:
    base_where = "WHERE v.id_reclutador = :rid"
    params = {"rid": reclutador_id}
    if vacante_id:
        base_where += " AND v.id = :vid"
        params["vid"] = vacante_id

    sql = f"""
        SELECT p.id AS postulacion_id, p.id_vacante AS vacante_id, v.titulo AS vacante, 
               p.fecha_postulacion, p.estado AS estado_postulacion,
               c.id AS candidato_id, u.id AS usuario_id, u.nombre, u.correo, c.cv_url,
               c.linkedin, c.portafolio,
               (SELECT e.puntaje FROM evaluaciones e WHERE e.id_postulacion = p.id ORDER BY e.fecha_evaluacion DESC LIMIT 1) AS puntaje,
               (SELECT e.nivel FROM evaluaciones e WHERE e.id_postulacion = p.id ORDER BY e.fecha_evaluacion DESC LIMIT 1) AS nivel,
               (SELECT e.fecha_evaluacion FROM evaluaciones e WHERE e.id_postulacion = p.id ORDER BY e.fecha_evaluacion DESC LIMIT 1) AS fecha_evaluacion
        FROM postulaciones p
        JOIN vacantes v ON v.id = p.id_vacante
        JOIN candidatos c ON c.id = p.id_candidato
        LEFT JOIN usuarios u ON u.id = c.usuario_id
        {base_where}
        ORDER BY p.fecha_postulacion DESC
    """
    rows = db.execute(text(sql), params).fetchall()
    data = [dict(r._mapping) for r in rows]
    for item in data:
        if item.get("cv_url"):
            item["cv_url"] = f"/cv/postulacion/{item['postulacion_id']}/archivo"
    return data

def _abs_url(u: Optional[str]) -> Optional[str]:
    if not u:
        return None
    if u.startswith("/cv/"):
        return u
    if u.startswith("http://") or u.startswith("https://"):
        return u
    u2 = u if u.startswith("/") else f"/{u}"
    if not u2.startswith("/uploads/") and not u2.startswith("/uploads\\"):
        u2 = "/uploads" + (u2 if u2.startswith("/") else f"/{u2}")
    return u2

@router.get("/postulaciones")
async def postulaciones_todas(db: Session = Depends(get_db), current_user: Usuario = Depends(require_recruiter), vacante_id: Optional[int] = None):
    reclutador = db.query(Reclutador).filter(Reclutador.id_usuario == current_user.id).first()
    if not reclutador:
        raise HTTPException(status_code=400, detail="Reclutador no encontrado")
    data = _fetch_postulaciones_recruiter(db, reclutador.id, vacante_id)
    for d in data:
        d["cv_url"] = _abs_url(d.get("cv_url"))
    return {"ok": True, "data": data}

@router.get("/vacantes/{vacante_id}/postulaciones")
async def postulaciones_por_vacante(vacante_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(require_recruiter)):
    reclutador = db.query(Reclutador).filter(Reclutador.id_usuario == current_user.id).first()
    if not reclutador:
        raise HTTPException(status_code=400, detail="Reclutador no encontrado")
    own = db.execute(text("SELECT 1 FROM vacantes WHERE id=:vid AND id_reclutador=:rid"), {"vid": vacante_id, "rid": reclutador.id}).fetchone()
    if not own:
        raise HTTPException(status_code=404, detail="Vacante no encontrada o no pertenece al reclutador")
    data = _fetch_postulaciones_recruiter(db, reclutador.id, vacante_id)
    for d in data:
        d["cv_url"] = _abs_url(d.get("cv_url"))
    return {"ok": True, "data": data}

# ==============================
# GENERAR PDF DE EVALUACIÓN
# ==============================
@router.get("/postulaciones/{postulacion_id}/evaluacion/pdf")
async def ver_evaluacion_pdf_reclutador(
    postulacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_recruiter)
):
    """
    Genera un PDF con la última evaluación de la postulación indicada
    para el reclutador propietario de la vacante.
    """
    # Traer postulación y vacante
    row = db.execute(text("""
        SELECT p.id AS postulacion_id, p.fecha_postulacion, p.estado AS estado_postulacion,
               u.nombre AS candidato_nombre, u.correo AS candidato_correo,
               v.titulo AS vacante, v.id_reclutador,
               e.puntaje, e.nivel, e.observacion, e.fecha_evaluacion, e.datos
        FROM postulaciones p
        LEFT JOIN evaluaciones e ON e.id_postulacion = p.id
        LEFT JOIN candidatos c ON c.id = p.id_candidato
        LEFT JOIN usuarios u ON u.id = c.usuario_id
        LEFT JOIN vacantes v ON p.id_vacante = v.id
        WHERE p.id = :pid
        ORDER BY e.fecha_evaluacion DESC
        LIMIT 1
    """), {"pid": postulacion_id}).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")

    recruiter = db.query(Reclutador).filter(Reclutador.id_usuario == current_user.id).first()
    is_admin = current_user.tipo == TipoUsuario.admin.value
    if not is_admin and (not recruiter or recruiter.id != row.id_reclutador):
        raise HTTPException(status_code=404, detail="Postulación no encontrada")

    # Valores por defecto si no hay evaluación
    puntaje = row.puntaje if row.puntaje is not None else "—"
    nivel = row.nivel if row.nivel else "—"
    observacion = row.observacion if row.observacion else "Aún no evaluado"
    fecha_eval = row.fecha_evaluacion if row.fecha_evaluacion else "—"

    # Crear PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            leftMargin=40, rightMargin=40, topMargin=60, bottomMargin=40)
    styles = getSampleStyleSheet()
    body_style = ParagraphStyle('Body', parent=styles['Normal'], leading=14, alignment=4)
    elements = []

    # Logo
    logo_path = "static/logo.png"
    if os.path.isfile(logo_path):
        elements.append(Image(logo_path, width=120, height=50))
        elements.append(Spacer(1, 12))

    elements.append(Paragraph("Reporte de Evaluación de Candidato", styles['Title']))
    elements.append(Spacer(1, 20))

    # Datos postulación
    data_postulacion = [
        ["Vacante:", row.vacante or "—"],
        ["Candidato:", row.candidato_nombre or "—"],
        ["Correo:", row.candidato_correo or "—"],
        ["Fecha postulación:", str(row.fecha_postulacion) if row.fecha_postulacion else "—"],
        ["Estado postulación:", row.estado_postulacion or "—"],
    ]
    table_post = Table(data_postulacion, colWidths=[150, 350])
    table_post.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ]))
    elements.append(Paragraph("<b>Datos de la postulación</b>", styles['Heading2']))
    elements.append(table_post)
    elements.append(Spacer(1, 20))

    # Datos evaluación
    data_eval = [
        ["Puntaje total:", str(puntaje)],
        ["Nivel:", str(nivel)],
        ["Fecha evaluación:", str(fecha_eval)],
    ]
    table_eval = Table(data_eval, colWidths=[150, 350])
    table_eval.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ]))
    elements.append(Paragraph("<b>Evaluación</b>", styles['Heading2']))
    elements.append(table_eval)
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("<b>Observaciones generales:</b>", styles['Normal']))
    elements.append(Paragraph(observacion, body_style))
    elements.append(Spacer(1, 20))

    # Detalle ítems desde datos JSON
    if row.datos:
        try:
            detalles_json = json.loads(row.datos)
            detalles = detalles_json.get("details", [])
            if detalles:
                elements.append(Paragraph("<b>Detalle por ítem</b>", styles['Heading2']))
                data_items = [["ID", "Puntaje", "Peso", "Comentarios"]]
                for d in detalles:
                    data_items.append([
                        d.get("id", ""),
                        str(d.get("score", 0)),
                        str(d.get("weight", 0)),
                        Paragraph(d.get("comments", ""), body_style),  # envuelve texto
                    ])
                table_items = Table(data_items, colWidths=[50, 50, 50, 320])
                table_items.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("ALIGN", (1, 1), (2, -1), "CENTER"),  # centra puntaje y peso
                ]))
                elements.append(table_items)
                elements.append(Spacer(1, 20))
        except Exception:
            elements.append(Paragraph("⚠ No se pudo mostrar el detalle de ítems.", styles['Normal']))

    # Footer
    fecha_gen = datetime.now().strftime("%d/%m/%Y %H:%M")
    elements.append(Spacer(1, 40))
    elements.append(Paragraph(
        f"<font size=8 color=grey>Reporte generado el {fecha_gen} por {current_user.nombre}</font>",
        styles['Normal']
    ))

    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=reporte_postulacion_{row.postulacion_id}.pdf"}
    )


# ==============================
# CAMBIAR ESTADO DE POSTULACIÓN
# ==============================
@router.post("/postulaciones/{postulacion_id}/estado")
async def cambiar_estado_postulacion(
    postulacion_id: int,
    payload: EstadoPostulacion = Body(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_recruiter)
):
    """
    Cambia el estado de la postulación (aceptado/rechazado) solo si el postulante pertenece
    a una vacante del reclutador.
    """
    # Verificar que la postulación pertenece al reclutador
    row = db.execute(
        text("""
            SELECT p.id
            FROM postulaciones p
            JOIN vacantes v ON v.id = p.id_vacante
            JOIN reclutadores r ON r.id = v.id_reclutador
            WHERE p.id = :pid AND r.id_usuario = :uid
        """),
        {"pid": postulacion_id, "uid": current_user.id}
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Postulación no encontrada o no pertenece al reclutador")

    # Actualizar estado
    db.execute(
        text("""
            UPDATE postulaciones
            SET estado = :estado
            WHERE id = :pid
        """),
        {"estado": payload.estado, "pid": postulacion_id}
    )
    db.commit()
    return {"ok": True, "message": f"Estado de la postulación actualizado a '{payload.estado}'"}
