# app/models/reclutador.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.db import Base

class Reclutador(Base):
    __tablename__ = "reclutadores"

    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    area_especialidad = Column(String(255), nullable=False)
    nombre = Column(String(255), nullable=False)
    correo = Column(String(255), nullable=False)
    telefono = Column(String(255), nullable=True)

    usuario = relationship("Usuario", back_populates="reclutador")
