import os
import time
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.security import get_current_user
from app.core.db import get_db
from app.models.usuario import Usuario, TipoUsuario
from app.models.reclutador import Reclutador

router = APIRouter()

# Carpeta donde guardar los CVs (se sirve por /uploads)
UPLOAD_ROOT = Path(os.getenv("UPLOAD_ROOT", "uploads")).resolve()
CV_DIR = UPLOAD_ROOT / "cv"
CV_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXT = {".pdf", ".doc", ".docx"}
MAX_BYTES = 5 * 1024 * 1024  # 5MB


@router.post("/upload")
async def upload_cv(
    file: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Solo candidatos
    if current_user.tipo != TipoUsuario.candidato.value:
        raise HTTPException(status_code=403, detail="Solo candidatos pueden subir CV")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="Formato no soportado (usa PDF/DOC/DOCX)")

    contents = await file.read(MAX_BYTES + 1)
    if len(contents) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="El archivo supera 5 MB")

    if ext == ".pdf" and not contents.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="El contenido no es un PDF válido")
    if ext in {".docx"} and not contents.startswith(b"PK\x03\x04"):
        raise HTTPException(status_code=400, detail="El contenido no es un DOCX válido")
    if ext == ".doc" and not contents.startswith(bytes.fromhex("D0CF11E0A1B11AE1")):
        raise HTTPException(status_code=400, detail="El contenido no es un DOC válido")

    ts = int(time.time())
    safe_name = f"{current_user.id}_{ts}{ext}"
    out_path = CV_DIR / safe_name
    with open(out_path, "wb") as f:
        f.write(contents)

    # URL pública
    # Se almacena solo la ruta privada, nunca una URL pública.
    url = f"cv/{out_path.name}"

    # Guardar en la DB
    db.execute(
        text("UPDATE candidatos SET cv_url = :u WHERE usuario_id = :uid"),
        {"u": url, "uid": current_user.id},
    )
    db.commit()

    return JSONResponse({"cv_url": url, "ok": True})


@router.get("/mio")
def get_my_cv(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.tipo != TipoUsuario.candidato.value:
        raise HTTPException(status_code=403, detail="Solo candidatos")

    row = db.execute(
        text("SELECT cv_url FROM candidatos WHERE usuario_id = :uid"),
        {"uid": current_user.id},
    ).fetchone()

    if not row or not row[0]:
        raise HTTPException(status_code=404, detail="No hay CV cargado")

    return {"cv_url": "/cv/mio/archivo"}


@router.get("/mio/archivo")
def download_my_cv(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.tipo != TipoUsuario.candidato.value:
        raise HTTPException(status_code=403, detail="Solo candidatos")
    row = db.execute(text("SELECT cv_url FROM candidatos WHERE usuario_id = :uid"), {"uid": current_user.id}).first()
    path = _stored_cv_path(row[0] if row else None)
    return FileResponse(path, filename=path.name, media_type="application/octet-stream")


@router.get("/postulacion/{postulacion_id}/archivo")
def download_cv_for_application(
    postulacion_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.execute(text("""
        SELECT c.cv_url, c.usuario_id, v.id_reclutador
        FROM postulaciones p
        JOIN candidatos c ON c.id = p.id_candidato
        JOIN vacantes v ON v.id = p.id_vacante
        WHERE p.id = :pid
    """), {"pid": postulacion_id}).first()
    if not row:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    is_candidate = current_user.tipo == TipoUsuario.candidato.value and row.usuario_id == current_user.id
    recruiter = db.query(Reclutador).filter(Reclutador.id_usuario == current_user.id).first()
    is_owner = current_user.tipo == TipoUsuario.reclutador.value and recruiter and recruiter.id == row.id_reclutador
    is_admin = current_user.tipo == TipoUsuario.admin.value
    if not (is_candidate or is_owner or is_admin):
        raise HTTPException(status_code=403, detail="No tienes permiso para descargar este CV")
    path = _stored_cv_path(row.cv_url)
    return FileResponse(path, filename=path.name, media_type="application/octet-stream")


@router.get("/admin/candidato/{candidato_id}/archivo")
def download_cv_admin(
    candidato_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.tipo != TipoUsuario.admin.value:
        raise HTTPException(status_code=403, detail="Solo administradores")
    row = db.execute(text("SELECT cv_url FROM candidatos WHERE id = :cid"), {"cid": candidato_id}).first()
    path = _stored_cv_path(row[0] if row else None)
    return FileResponse(path, filename=path.name, media_type="application/octet-stream")


def _stored_cv_path(url):
    name = Path(url or "").name
    if not name or name in {".", ".."}:
        raise HTTPException(status_code=404, detail="No hay CV cargado")
    path = (CV_DIR / name).resolve()
    if path.parent != CV_DIR or not path.is_file():
        raise HTTPException(status_code=404, detail="CV no encontrado")
    return path
