from enum import Enum

class TipoUsuario(str, Enum):
    admin = "admin"
    reclutador = "reclutador"
    candidato = "candidato"
