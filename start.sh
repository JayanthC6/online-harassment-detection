#!/usr/bin/env bash
set -e

echo "========================================================"
echo "       ShieldAI - Cyber Threat Intelligence Platform"
echo "                Starting Backend & Frontend"
echo "========================================================"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Activate venv if it exists
if [ -d "venv/bin" ]; then
    source venv/bin/activate
fi

echo "[1/2] Launching Backend on http://127.0.0.1:5000 ..."
(cd backend && python3 app.py) &
BACKEND_PID=$!

echo "[2/2] Launching Frontend on http://localhost:5173 ..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

cleanup() {
    echo "Stopping ShieldAI services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo ""
echo "========================================================"
echo "ShieldAI is up and running!"
echo "- Web App: http://localhost:5173"
echo "- Backend: http://127.0.0.1:5000"
echo "========================================================"

wait $BACKEND_PID $FRONTEND_PID

