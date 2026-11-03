# app/main.py
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api import auth, postulaciones, cv, evaluacion
from app.api import admin as admin_api
from app.api import recruiter as recruiter_api
from app.api import vacantes
from app.api import candidate as candidate_api 
import os

# -------------------------------------------------
# App
# -------------------------------------------------
production = os.getenv("APP_ENV", "development").lower() == "production"
app = FastAPI(
    title="Plataforma de Selección de Talento IA (MySQL)",
    docs_url=None if production else "/docs",
    redoc_url=None if production else "/redoc",
    openapi_url=None if production else "/openapi.json",
)

# -------------------------------------------------
# CORS
# -------------------------------------------------
allowed_origins = [
    origin.strip() for origin in os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080"
    ).split(",") if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# -------------------------------------------------
# Routers
# -------------------------------------------------
app.include_router(auth.router,           prefix="/auth",         tags=["Auth"])
app.include_router(vacantes.router,       prefix="/vacantes",     tags=["Vacantes"])
app.include_router(postulaciones.router,  prefix="/postulaciones",tags=["Postulaciones"])
app.include_router(cv.router,             prefix="/cv",           tags=["CV"])
#app.include_router(evaluacion.router,     prefix="/postulaciones/evaluacion", tags=["Evaluación IA"])

app.include_router(admin_api.router,      prefix="/admin",        tags=["Admin"])
app.include_router(recruiter_api.router,  prefix="/reclutador",   tags=["Reclutador"])
app.include_router(candidate_api.router,  prefix="/candidate",    tags=["Candidate"])

# -------------------------------------------------
# Estáticos
# -------------------------------------------------
# Los CV contienen datos personales y nunca deben exponerse como archivos públicos.

# -------------------------------------------------
# Healthcheck rápido
# -------------------------------------------------
@app.get("/healthz", tags=["Health"])
async def healthz():
    return {"status": "ok"}

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    if production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# -------------------------------------------------
# Manejador de errores genérico
# -------------------------------------------------
@app.exception_handler(Exception)
async def all_exception_handler(request: Request, exc: Exception):
    print("[ERROR]", repr(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Ha ocurrido un error inesperado."},
    )

# -------------------------------------------------
# Entrypoint
# -------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8443, reload=True)
