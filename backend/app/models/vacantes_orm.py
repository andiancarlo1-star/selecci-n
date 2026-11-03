from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from app.core.db import Base
from datetime import datetime

class Vacante(Base):
    __tablename__ = "vacantes"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    descripcion = Column(String, nullable=False)
    requisitos = Column(String, nullable=True)  # <- Asegúrate de que exista
    salario_min = Column(Float, nullable=True)
    salario_max = Column(Float, nullable=True)
    ubicacion = Column(String, nullable=True)
    modalidad = Column(String, nullable=True)
    estado = Column(String, nullable=False)
    fecha_publicacion = Column(DateTime, nullable=True)
    id_reclutador = Column(Integer, nullable=False)

    # Relación con postulaciones
    postulaciones = relationship("Postulacion", back_populates="vacante")
