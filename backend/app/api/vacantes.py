# app/api/vacantes.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.db import get_db  # Tu dependencia de sesión de DB
from app.models.vacantes_orm import Vacante  # Tu modelo ORM de Vacante
from app.core.security import get_current_user
from app.models.usuario import Usuario, TipoUsuario
from app.models.reclutador import Reclutador

router = APIRouter()

# ======================
# Pydantic Models
# ======================
from pydantic import BaseModel
from enum import Enum

class EstadoVacanteEnum(str, Enum):
    activa = "activa"
    inactiva = "inactiva"
    cerrada = "cerrada"

class VacanteBase(BaseModel):
    id: int
    titulo: str
    descripcion: str | None
    requisitos: str | None
    salario_min: float | None
    salario_max: float | None
    ubicacion: str | None
    modalidad: str | None
    estado: EstadoVacanteEnum
    fecha_publicacion: datetime
    id_reclutador: int

    class Config:
        from_attributes = True  # Para Pydantic v2 (equivalente a orm_mode)

# ======================
# Endpoints
# ======================

@router.get("/listar", response_model=List[VacanteBase])
def listar_vacantes(db: Session = Depends(get_db)):
    vacantes = db.query(Vacante).all()
    return vacantes

@router.get("/mis-vacantes", response_model=List[VacanteBase])
def mis_vacantes(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    recruiter = db.query(Reclutador).filter(Reclutador.id_usuario == current_user.id).first()
    if current_user.tipo != TipoUsuario.reclutador.value or not recruiter:
        raise HTTPException(status_code=403, detail="Solo reclutadores pueden ver sus vacantes")
    vacantes = db.query(Vacante).filter(Vacante.id_reclutador == recruiter.id).all()
    return vacantes

@router.put("/cerrar/{vacante_id}")
def cerrar_vacante(vacante_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    recruiter = db.query(Reclutador).filter(Reclutador.id_usuario == current_user.id).first()
    if current_user.tipo != TipoUsuario.reclutador.value or not recruiter:
        raise HTTPException(status_code=403, detail="Solo reclutadores pueden modificar vacantes")
    vacante = db.query(Vacante).filter(Vacante.id == vacante_id, Vacante.id_reclutador == recruiter.id).first()
    if not vacante:
        raise HTTPException(status_code=404, detail="Vacante no encontrada")
    vacante.estado = "cerrada"
    db.commit()
    db.refresh(vacante)
    return {"message": "Vacante cerrada con éxito"}

@router.put("/abrir/{vacante_id}")
def abrir_vacante(vacante_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    recruiter = db.query(Reclutador).filter(Reclutador.id_usuario == current_user.id).first()
    if current_user.tipo != TipoUsuario.reclutador.value or not recruiter:
        raise HTTPException(status_code=403, detail="Solo reclutadores pueden modificar vacantes")
    vacante = db.query(Vacante).filter(Vacante.id == vacante_id, Vacante.id_reclutador == recruiter.id).first()
    if not vacante:
        raise HTTPException(status_code=404, detail="Vacante no encontrada")
    vacante.estado = "activa"
    db.commit()
    db.refresh(vacante)
    return {"message": "Vacante abierta con éxito"}

@router.post("/crear", response_model=VacanteBase)
def crear_vacante(
    titulo: str,
    descripcion: str | None = None,
    requisitos: str | None = None,
    salario_min: float | None = None,
    salario_max: float | None = None,
    ubicacion: str | None = None,
    modalidad: str | None = "presencial",
    id_reclutador: int = 1,  # se puede ajustar según el usuario
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    recruiter = db.query(Reclutador).filter(Reclutador.id_usuario == current_user.id).first()
    if current_user.tipo != TipoUsuario.reclutador.value or not recruiter:
        raise HTTPException(status_code=403, detail="Solo reclutadores pueden crear vacantes")
    nueva_vacante = Vacante(
        titulo=titulo,
        descripcion=descripcion,
        requisitos=requisitos,
        salario_min=salario_min,
        salario_max=salario_max,
        ubicacion=ubicacion,
        modalidad=modalidad,
        estado="activa",
        fecha_publicacion=datetime.now(),
        id_reclutador=recruiter.id
    )
    db.add(nueva_vacante)
    db.commit()
    db.refresh(nueva_vacante)
    return nueva_vacante
