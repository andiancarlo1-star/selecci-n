from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from app.core.db import get_db
from app.models.usuario import Usuario, TipoUsuario
from app.core.security import get_current_user
from app.models.reclutador import Reclutador
from app.models.candidato import Candidato

router = APIRouter()

# Candidato aplica a una vacante
@router.post("/aplicar")
def aplicar_vacante(
    vacante_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Solo candidatos pueden aplicar
    if current_user.tipo != TipoUsuario.candidato.value:
        raise HTTPException(status_code=403, detail="Solo los candidatos pueden postularse")

    # Verificar que la vacante exista y esté activa
    vacante = db.execute(text("SELECT * FROM vacantes WHERE id = :id"), {"id": vacante_id}).fetchone()
    if not vacante:
        raise HTTPException(status_code=404, detail="Vacante no encontrada")
    if vacante.estado != "activa":
        raise HTTPException(status_code=400, detail="No puedes postularte a una vacante cerrada o inactiva")

    # Verificar si el usuario ya existe en la tabla candidatos, sino insertarlo
    candidato = db.query(Candidato).filter(Candidato.usuario_id == current_user.id).first()
    if not candidato:
        candidato = Candidato(usuario_id=current_user.id)
        db.add(candidato)
        db.commit()
        db.refresh(candidato)

    # Verificar si ya aplicó antes
    ya_aplico = db.execute(text(
        "SELECT * FROM postulaciones WHERE id_candidato = :id_candidato AND id_vacante = :id_vacante"
    ), {"id_candidato": candidato.id, "id_vacante": vacante_id}).fetchone()

    if ya_aplico:
        raise HTTPException(status_code=400, detail="Ya aplicaste a esta vacante")

    # Insertar la postulación
    query = text("""
        INSERT INTO postulaciones (id_candidato, id_vacante, fecha_postulacion, estado)
        VALUES (:id_candidato, :id_vacante, :fecha_postulacion, 'pendiente')
    """)
    db.execute(query, {
        "id_candidato": candidato.id,
        "id_vacante": vacante_id,
        "fecha_postulacion": datetime.now()
    })
    db.commit()

    return {"message": "Postulación enviada con éxito"}

# Reclutador ve postulaciones a sus vacantes
@router.get("/mis-vacantes")
def ver_postulaciones_reclutador(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.tipo != TipoUsuario.reclutador.value:
        raise HTTPException(status_code=403, detail="Solo los reclutadores pueden ver postulaciones")

    query = text("""
        SELECT p.id AS id_postulacion, u.nombre AS candidato, u.correo, v.titulo AS vacante, p.estado, p.fecha_postulacion
        FROM postulaciones p
        JOIN usuarios u ON p.id_candidato = u.id
        JOIN vacantes v ON p.id_vacante = v.id
        WHERE v.id_reclutador = :id_reclutador
    """)
    recruiter = db.query(Reclutador).filter(Reclutador.id_usuario == current_user.id).first()
    if not recruiter:
        raise HTTPException(status_code=403, detail="Reclutador no encontrado")
    result = db.execute(query, {"id_reclutador": recruiter.id}).fetchall()
    return [dict(row._mapping) for row in result]

# Admin ve TODAS las postulaciones
@router.get("/todas")
def ver_todas_postulaciones(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.tipo != TipoUsuario.admin.value:
        raise HTTPException(status_code=403, detail="Solo el admin puede ver todas las postulaciones")

    query = text("""
        SELECT p.id AS id_postulacion, u.nombre AS candidato, u.correo, v.titulo AS vacante, p.estado, p.fecha_postulacion
        FROM postulaciones p
        JOIN usuarios u ON p.id_candidato = u.id
        JOIN vacantes v ON p.id_vacante = v.id
    """)
    result = db.execute(query).fetchall()
    return [dict(row._mapping) for row in result]

@router.put("/cambiar-estado/{postulacion_id}")
def cambiar_estado_postulacion(
    postulacion_id: int,
    nuevo_estado: str = Form(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Solo reclutadores o admin pueden cambiar estados
    if current_user.tipo not in [TipoUsuario.reclutador.value, TipoUsuario.admin.value]:
        raise HTTPException(status_code=403, detail="No tienes permisos para cambiar el estado de postulaciones")

    # Verificamos que la postulación exista
    postulacion = db.execute(text("""
        SELECT p.*, v.id_reclutador FROM postulaciones p
        JOIN vacantes v ON p.id_vacante = v.id
        WHERE p.id = :id
    """), {"id": postulacion_id}).fetchone()

    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")

    # Si es reclutador, solo puede modificar postulaciones de sus vacantes
    recruiter = db.query(Reclutador).filter(Reclutador.id_usuario == current_user.id).first()
    if current_user.tipo == TipoUsuario.reclutador.value and (not recruiter or postulacion.id_reclutador != recruiter.id):
        raise HTTPException(status_code=403, detail="No puedes modificar postulaciones de vacantes de otro reclutador")

    # Validar que el nuevo estado sea uno de los permitidos
    estados_permitidos = ["pendiente", "evaluado", "aceptado", "rechazado"]
    if nuevo_estado not in estados_permitidos:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Usa: {', '.join(estados_permitidos)}")

    # Actualizamos el estado
    db.execute(text("UPDATE postulaciones SET estado = :estado WHERE id = :id"),
               {"estado": nuevo_estado, "id": postulacion_id})
    db.commit()

    return {"message": f"Estado de la postulación actualizado a '{nuevo_estado}' con éxito"}

@router.get("/ver-cv/{postulacion_id}")
def ver_cv_postulante(
    postulacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Solo reclutadores o admin pueden ver CV
    if current_user.tipo not in [TipoUsuario.reclutador.value, TipoUsuario.admin.value]:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver CV")

    # Buscar la postulación y verificar si pertenece a una vacante del reclutador
    postulacion = db.execute(text("""
        SELECT p.id_candidato, v.id_reclutador 
        FROM postulaciones p
        JOIN vacantes v ON p.id_vacante = v.id
        WHERE p.id = :id
    """), {"id": postulacion_id}).fetchone()

    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")

    # Si es reclutador, solo puede ver CV de sus vacantes
    recruiter = db.query(Reclutador).filter(Reclutador.id_usuario == current_user.id).first()
    if current_user.tipo == TipoUsuario.reclutador.value and (not recruiter or postulacion.id_reclutador != recruiter.id):
        raise HTTPException(status_code=403, detail="No puedes ver CV de candidatos que no aplicaron a tus vacantes")

    # Buscar el CV en la tabla candidatos
    candidato = db.execute(text("SELECT cv_url FROM candidatos WHERE id = :id"), 
                           {"id": postulacion.id_candidato}).fetchone()

    if not candidato or not candidato.cv_url:
        raise HTTPException(status_code=404, detail="El candidato no tiene un CV subido")

    return {"cv_url": candidato.cv_url}
