from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from app.core.db import get_db
from app.models.usuario import Usuario, TipoUsuario
from app.core.security import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter()

# ======== Schemas ========
class LoginRequest(BaseModel):
    correo: EmailStr
    contrasena: str = Field(min_length=1, max_length=72)

class RegisterRequest(BaseModel):
    nombre: str = Field(min_length=1, max_length=255)
    correo: EmailStr
    contrasena: str = Field(min_length=12, max_length=72)

class UserOut(BaseModel):
    id: int
    nombre: str
    correo: EmailStr
    tipo: str

class TokenOut(BaseModel):
    ok: bool
    access_token: str
    token_type: str
    role: str

class OkUserOut(BaseModel):
    ok: bool
    message: str
    user: UserOut

class MeOut(BaseModel):
    ok: bool
    user: UserOut

# ======== Helpers ========
def _tipo_to_str(tipo_val) -> str:
    return str(getattr(tipo_val, "value", tipo_val))

def _user_to_out(u: Usuario) -> UserOut:
    return UserOut(
        id=u.id,
        nombre=u.nombre,
        correo=u.correo,
        tipo=_tipo_to_str(u.tipo),
    )

# ======== Endpoints ========
from app.models.candidato import Candidato

@router.post("/register", response_model=OkUserOut, status_code=status.HTTP_201_CREATED)
def register_json(
    data: RegisterRequest = Body(...),
    db: Session = Depends(get_db)
):
    # Validar correo existente
    if db.query(Usuario).filter(Usuario.correo == data.correo).first():
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    
    # Crear usuario con tipo por defecto "postulante"
    user = Usuario(
        nombre=data.nombre,
        correo=data.correo,
        contrasena=hash_password(data.contrasena),
        tipo=TipoUsuario.candidato.value  # tipo por defecto
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Crear registro en tabla de candidatos
    candidato = Candidato(
        usuario_id=user.id,
        cv_url=None,
        linkedin=None,
        portafolio=None
    )
    db.add(candidato)
    db.commit()
    db.refresh(candidato)
    
    return {"ok": True, "message": "Registro exitoso", "user": _user_to_out(user)}


@router.post("/login", response_model=TokenOut)
def login(data: LoginRequest = Body(...), db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.correo == data.correo).first()
    if not user or not verify_password(data.contrasena, user.contrasena):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    role = user.tipo
    access_token = create_access_token(
        data={"sub": user.correo, "role": role}
    )

    return {"ok": True, "access_token": access_token, "token_type": "bearer", "role": role}

@router.get("/me", response_model=MeOut)
def me(current_user: Usuario = Depends(get_current_user)):
    return {"ok": True, "user": _user_to_out(current_user)}
