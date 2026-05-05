#!/bin/bash
# PerilCar ERP — Dev Server Start Script
# Uso: bash start.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "  PerilCar ERP — Gestionale Aziendale"
echo "  Ing. Carmine Perillo"
echo "  ===================================="
echo ""

# ── Trova Python 3 ───────────────────────────────────────────────────
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "  [ERRORE] Python non trovato."
    echo "  Installa Python 3.11+ da https://www.python.org"
    exit 1
fi

PYVER=$($PYTHON --version 2>&1)
echo "  Python: $PYVER"

# ── Dipendenze ───────────────────────────────────────────────────────
echo "  Controllo dipendenze..."
if ! $PYTHON -c "import flask, flask_socketio, watchdog" &>/dev/null; then
    echo "  Installazione dipendenze..."
    pip install flask flask-socketio watchdog customtkinter pillow --quiet
    echo "  Dipendenze installate."
else
    echo "  Dipendenze OK."
fi

echo ""
echo "  ===================================="
echo "   Dev Server: http://localhost:5000"
echo "   Login:      admin / admin123"
echo "   Stop:       CTRL+C"
echo "  ===================================="
echo ""

$PYTHON dev_server.py
