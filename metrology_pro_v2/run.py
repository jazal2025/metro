#!/usr/bin/env python3
"""
Metrology Pro — Launcher
Lanzador multiplataforma (Windows / Linux / macOS).
Instala dependencias, inicializa la BD y abre el navegador.
"""

import subprocess
import sys
import os
import webbrowser
import time
import threading
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8000
APP_DIR = Path(__file__).resolve().parent


def install_deps():
    """Instala dependencias desde requirements.txt si faltan."""
    req_file = APP_DIR / "requirements.txt"
    if not req_file.exists():
        print("[!] requirements.txt no encontrado.")
        return

    print("[*] Verificando dependencias...")
    try:
        import fastapi, uvicorn, numpy  # noqa
        print("[✓] Dependencias ya instaladas.")
    except ImportError:
        print("[*] Instalando dependencias...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(req_file), "--quiet"
        ])
        print("[✓] Dependencias instaladas.")


def open_browser():
    """Abre el navegador tras un breve retardo."""
    time.sleep(1.5)
    url = f"http://{HOST}:{PORT}"
    print(f"\n[✓] Abriendo navegador en {url}")
    webbrowser.open(url)


def main():
    os.chdir(APP_DIR)
    print("=" * 52)
    print("  METROLOGY PRO — ISO 10360-2 / VDI/VDE 2617")
    print("=" * 52)

    install_deps()

    # Abrir navegador en hilo separado
    threading.Thread(target=open_browser, daemon=True).start()

    print(f"\n[*] Iniciando servidor en {HOST}:{PORT}")
    print("[*] Presiona Ctrl+C para detener.\n")

    # Ejecutar uvicorn
    try:
        import uvicorn
        uvicorn.run("app.main:app", host=HOST, port=PORT, reload=False)
    except KeyboardInterrupt:
        print("\n[*] Servidor detenido.")


if __name__ == "__main__":
    main()
