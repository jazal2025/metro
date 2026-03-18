@echo off
title Metrology Pro
echo ====================================================
echo   METROLOGY PRO - Iniciando...
echo ====================================================
echo.
python run.py
if errorlevel 1 (
    echo.
    echo [!] Error: Asegurate de tener Python 3.10+ instalado.
    echo     Descargalo en https://www.python.org/downloads/
    pause
)
