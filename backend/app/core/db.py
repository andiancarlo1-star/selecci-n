import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# La URL se inyecta por entorno en Docker; se conserva este valor para desarrollo local.
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", "mysql+pymysql://root@localhost/talento_ia_sistema?charset=utf8mb4"
)

# Crear motor de base de datos
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, connect_args={"charset": "utf8mb4"})

# Crear sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative Base
Base = declarative_base()

# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
