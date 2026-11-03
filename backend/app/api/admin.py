# admin.py
from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional, Literal, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, EmailStr, Field
from passlib.context import CryptContext
from sqlalchemy import text
from app.core.security import get_current_user
from app.core.db import get_db
from app.models.usuario import Usuario, TipoUsuario
from app.models.reclutador import Reclutador
from app.models.vacantes_orm import Vacante
from app.models.postulaciones import Postulacion

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter()


# =========================
# Pydantic Models
# =========================

class UsuarioBase(BaseModel):
    nombre: str
    correo: str
    tipo: TipoUsuario

    class Config:
        from_attributes = True


class VacanteBase(BaseModel):
    id: int
    titulo: str
    descripcion: Optional[str] = None
    requisitos: Optional[str] = None
    salario_min: Optional[float] = None
    salario_max: Optional[float] = None
    ubicacion: Optional[str] = None
    modalidad: Optional[str] = None
    estado: str
    fecha_publicacion: Optional[str] = None
    id_reclutador: int

    class Config:
        from_attributes = True

# =========================
# Modelo de Postulación Detallada
# =========================
class PostulacionDetalle(BaseModel):
    id: int
    candidato_id: int
    candidato_nombre: str
    candidato_correo: str
    vacante_id: int
    vacante_titulo: str
    estado: str
    fecha_postulacion: str   # o datetime si lo quieres como objeto de fecha

    class Config:
        from_attributes = True

class PagedPostulacionesResponse(BaseModel):
    items: List[PostulacionDetalle]
    page: int
    page_size: int
    total: int
    pages: int

class CreateReclutadorRequest(BaseModel):
    nombre: str = Field(min_length=1, max_length=255)
    correo: EmailStr
    contrasena: str = Field(min_length=12, max_length=72)
    area_especialidad: str = Field(min_length=1, max_length=255)
    telefono: Optional[str] = Field(default=None, max_length=40)


# --- Modelo de item candidato y respuesta paginada ---
class CandidatoItem(BaseModel):
    id: int
    nombre: str
    correo: str
    telefono: Optional[str] = None
    estado: Literal["activo", "inactivo"]
    fecha_creacion: Optional[str] = None
    reclutador_id: Optional[int] = None
    area_especialidad: Optional[str] = None

    class Config:
        from_attributes = True


class PagedCandidatosResponse(BaseModel):
    items: List[CandidatoItem]
    page: int
    page_size: int
    total: int
    pages: int


# =========================
# Dependencias
# =========================

def require_admin(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if current_user.tipo != TipoUsuario.admin.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden realizar esta acción"
        )
    return current_user


# =========================
# Endpoints - Admin
# =========================

@router.get("/vacantes", response_model=List[VacanteBase])
def get_vacantes_admin(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    vacantes = db.query(Vacante).all()
    return [
        VacanteBase(
            id=v.id,
            titulo=v.titulo,
            descripcion=v.descripcion,
            requisitos=v.requisitos,
            salario_min=v.salario_min,
            salario_max=v.salario_max,
            ubicacion=v.ubicacion,
            modalidad=v.modalidad,
            estado=v.estado,
            fecha_publicacion=(
                v.fecha_publicacion.strftime("%Y-%m-%d %H:%M:%S")
                if v.fecha_publicacion else None
            ),
            id_reclutador=v.id_reclutador
        )
        for v in vacantes
    ]


@router.get("/reclutadores")
def get_reclutadores(db: Session = Depends(get_db), current_user: Usuario = Depends(require_admin)):
    reclutadores = db.query(Reclutador).all()
    result = []
    for r in reclutadores:
        usuario = db.query(Usuario).filter(Usuario.id == r.id_usuario).first()
        result.append({
            "reclutador_id": r.id,      # <- este id usaremos para eliminar
            "usuario_id": usuario.id,
            "nombre": usuario.nombre,
            "correo": usuario.correo,
            "area_especialidad": r.area_especialidad or '',
            "telefono": r.telefono or ''
        })
    return result


# =========================
# Listar CANDIDATOS (paginado + búsqueda + filtros)
# =========================
@router.get("/candidatos", response_model=List[Dict[str, Any]])
async def ver_candidatos_admin(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str = Query(None, description="Buscar por nombre o correo"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
):
    offset = (page - 1) * page_size
    search_filter = f"%{q}%" if q else "%"

    sql = """
    SELECT 
        c.id,
        u.nombre,
        u.correo,
        CASE WHEN c.cv_url IS NOT NULL THEN CONCAT('/cv/admin/candidato/', c.id, '/archivo') ELSE NULL END AS cv_url,
        c.linkedin,
        c.portafolio
    FROM candidatos c
    LEFT JOIN usuarios u ON u.id = c.usuario_id
    WHERE u.nombre LIKE :search OR u.correo LIKE :search
    ORDER BY u.nombre ASC
    LIMIT :limit OFFSET :offset
    """

    params = {"search": search_filter, "limit": page_size, "offset": offset}
    rows = db.execute(text(sql), params).fetchall()
    return [dict(r._mapping) for r in rows]

# =========================
# Crear reclutador
# =========================
@router.post("/create-recruiter", status_code=status.HTTP_201_CREATED)
def create_reclutador(
    data: CreateReclutadorRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    # Verificar correo duplicado
    if db.query(Usuario).filter(Usuario.correo == data.correo).first():
        raise HTTPException(status_code=400, detail="Correo ya registrado")

    hashed_password = pwd_context.hash(data.contrasena)

    # Crear usuario
    nuevo_usuario = Usuario(
        nombre=data.nombre,
        correo=data.correo,
        contrasena=hashed_password,
        tipo=TipoUsuario.reclutador.value
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    # Crear reclutador relacionado al usuario
    nuevo_reclutador = Reclutador(
        nombre=data.nombre,
        correo=data.correo,
        area_especialidad=data.area_especialidad,
        telefono=data.telefono,
        id_usuario=nuevo_usuario.id
    )
    db.add(nuevo_reclutador)
    db.commit()
    db.refresh(nuevo_reclutador)

    return {
        "message": "Reclutador creado correctamente",
        "usuario_id": nuevo_usuario.id,
        "reclutador_id": nuevo_reclutador.id
    }


# =========================
# Eliminar reclutador
# =========================
@router.delete("/delete-recruiter/{reclutador_id}")
def delete_recruiter(
    reclutador_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    # Buscar el reclutador en la tabla reclutadores
    reclutador = db.query(Reclutador).filter(Reclutador.id == reclutador_id).first()
    if not reclutador:
        raise HTTPException(status_code=404, detail="Reclutador no encontrado")

    # Buscar el usuario asociado
    usuario = db.query(Usuario).filter(Usuario.id == reclutador.id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario asociado no encontrado")

    # Eliminar ambos
    db.delete(reclutador)
    db.delete(usuario)
    db.commit()

    return {"message": f"Reclutador '{reclutador.nombre}' eliminado correctamente"}


# ----------------------------
# Aquí va tu nuevo endpoint
# ----------------------------
@router.get("/postulaciones-detalle", response_model=List[Dict[str, Any]])
async def ver_postulaciones_admin_detalle(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
):
    offset = (page - 1) * page_size

    sql = """
    SELECT 
        p.id AS id,
        p.id_vacante AS vacante_id,
        v.titulo AS vacante,
        p.fecha_postulacion,
        p.estado AS estado,
        c.id AS candidato_id,
        u.nombre AS candidato_nombre,
        u.correo AS candidato_correo,
        CASE WHEN c.cv_url IS NOT NULL THEN CONCAT('/cv/admin/candidato/', c.id, '/archivo') ELSE NULL END AS cv_url,
        c.linkedin,
        c.portafolio,
        (SELECT e.puntaje FROM evaluaciones e WHERE e.id_postulacion = p.id ORDER BY e.fecha_evaluacion DESC LIMIT 1) AS puntaje,
        (SELECT e.nivel FROM evaluaciones e WHERE e.id_postulacion = p.id ORDER BY e.fecha_evaluacion DESC LIMIT 1) AS nivel,
        (SELECT e.fecha_evaluacion FROM evaluaciones e WHERE e.id_postulacion = p.id ORDER BY e.fecha_evaluacion DESC LIMIT 1) AS fecha_evaluacion
    FROM postulaciones p
    LEFT JOIN vacantes v ON v.id = p.id_vacante
    LEFT JOIN candidatos c ON c.id = p.id_candidato
    LEFT JOIN usuarios u ON u.id = c.usuario_id
    ORDER BY p.fecha_postulacion DESC
    LIMIT :limit OFFSET :offset
    """

    params = {"limit": page_size, "offset": offset}
    rows = db.execute(text(sql), params).fetchall()
    return [dict(r._mapping) for r in rows]

@router.delete("/delete-vacante/{vacante_id}")
def delete_vacante(
    vacante_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    vacante = db.query(Vacante).filter(Vacante.id == vacante_id).first()
    if not vacante:
        raise HTTPException(status_code=404, detail="Vacante no encontrada")

    # Eliminar postulaciones relacionadas
    db.query(Postulacion).filter(Postulacion.id_vacante == vacante_id).delete(synchronize_session=False)

    # Eliminar la vacante
    db.delete(vacante)
    db.commit()

    return {"message": f"Vacante '{vacante.titulo}' y sus postulaciones eliminadas correctamente"}
