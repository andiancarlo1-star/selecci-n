from sqlalchemy import Column, Integer, String, ForeignKey
from app.core.db import Base

class Candidato(Base):
    __tablename__ = "candidatos"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)  # <- referencia a Usuario
    cv_url = Column(String, nullable=True)
    linkedin = Column(String, nullable=True)
    portafolio = Column(String, nullable=True)
