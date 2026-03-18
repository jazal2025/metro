"""
Metrology Pro — Aplicación principal
Sistema de gestión metrológica conforme a ISO 10360-2 / VDI/VDE 2617.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path

from app.db import init_db
from app.routers import calibration, upload, report, history, analysis

APP_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Metrology Pro",
    version="2.0.0",
    description="Sistema de calibración y verificación metrológica — ISO 10360-2 / VDI/VDE 2617",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar BD
init_db()

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
    return HTMLResponse("<h1>Metrology Pro API</h1><p>Frontend no encontrado. Visita <a href='/docs'>/docs</a>.</p>")


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}
