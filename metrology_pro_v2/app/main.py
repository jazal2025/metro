"""
Metrology Pro — Aplicación principal
Sistema de gestión metrológica conforme a ISO 10360-2 / VDI/VDE 2617.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
import os
import logging

from app.db import init_db
from app.routers import calibration, upload, report, history, analysis

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

APP_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Metrology Pro",
    version="2.0.0",
    description="Sistema de calibración y verificación metrológica — ISO 10360-2 / VDI/VDE 2617",
)

# Configuración de CORS desde variables de entorno
# En producción: ALLOWED_HOSTS="127.0.0.1,localhost" o especificar dominios reales
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS if host.strip()]

logger.info(f"CORS allowed hosts: {ALLOWED_HOSTS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_HOSTS,
    allow_credentials=False,  # False en producción por seguridad
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Accept"],
    max_age=600,  # Cache preflight por 10 minutos
)

# Inicializar BD
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    raise

# Routers API
app.include_router(calibration.router)
app.include_router(upload.router)
app.include_router(report.router)
app.include_router(history.router)
app.include_router(analysis.router)

# Servir archivos estáticos
static_dir = APP_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    index = static_dir / "index.html"
    if index.exists():
        return index.read_text(encoding="utf-8")
    return HTMLResponse(
        "<h1>Metrology Pro API</h1>"
        "<p>Frontend no encontrado. Visita <a href='/docs'>/docs</a> para la documentación.</p>"
    )

@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "2.0.0"}

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Manejador global de excepciones."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return {"detail": "Internal server error", "status": 500}