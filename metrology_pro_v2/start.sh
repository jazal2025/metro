#!/bin/bash
echo "===================================================="
echo "  METROLOGY PRO - Iniciando..."
echo "===================================================="
echo ""
python3 run.py || {
    echo ""
    echo "[!] Error: Asegúrate de tener Python 3.10+ instalado."
    echo "    sudo apt install python3 python3-pip  (Debian/Ubuntu)"
    echo "    sudo dnf install python3 python3-pip  (Fedora/RHEL)"
}
