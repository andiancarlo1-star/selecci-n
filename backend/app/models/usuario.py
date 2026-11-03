from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from enum import Enum
from app.core.db import Base

class TipoUsuario(Enum):
    admin = "admin"
    reclutador = "reclutador"
    candidato = "candidato"

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    correo = Column(String, unique=True, index=True, nullable=False)
    contrasena = Column(String, nullable=False)
    area_especialidad = Column(String, nullable=True)
    tipo = Column(String, default=TipoUsuario.candidato.value)

    # Relación con postulaciones
    postulaciones = relationship("Postulacion", back_populates="usuario")
    reclutador = relationship("Reclutador", back_populates="usuario", uselist=False)
