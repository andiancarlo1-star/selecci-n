from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.core.db import Base

class Postulacion(Base):
    __tablename__ = "postulaciones"

    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"))
    id_vacante = Column(Integer, ForeignKey("vacantes.id"))

    # Relaciones
    usuario = relationship("Usuario", back_populates="postulaciones")
    vacante = relationship("Vacante", back_populates="postulaciones")
