#!/usr/bin/env bash
set -e

echo "============================================================================"
echo "  ShieldAI - Setup & Installation Script (Linux / macOS)"
echo "============================================================================"

# 1. Detect Python
if command -v python3 >/dev/null 2>&1; then
    PY_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PY_CMD="python"
else
    echo "[ERROR] Python 3 is not installed or not in PATH."
    exit 1
fi

echo "[*] Using Python: $($PY_CMD --version)"

# 2. Virtual Environment
if [ ! -d "venv" ]; then
    echo "[*] Creating virtual environment 'venv'..."
    $PY_CMD -m venv venv
else
    echo "[*] Virtual environment 'venv' already exists."
fi

source venv/bin/activate

# 3. Install Python Dependencies
echo "[*] Installing backend dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r backend/requirements.txt

# 4. Frontend Dependencies
if command -v npm >/dev/null 2>&1; then
    echo "[*] Installing frontend dependencies..."
    (cd frontend && npm install)
else
    echo "[WARN] npm not found on PATH. Skipping frontend npm install."
fi

# 5. Seed Demo Database
echo "[*] Initializing demo SQLite database..."
python scripts/reset_demo.py

# 6. Run System Doctor
echo "[*] Running ShieldAI System Doctor..."
python scripts/doctor.py

echo ""
echo "============================================================================"
echo "  ShieldAI Setup Complete!"
echo ""
echo "  To start the backend:"
echo "    source venv/bin/activate && python backend/app.py"
echo ""
echo "  To start the frontend:"
echo "    cd frontend && npm run dev"
echo ""
echo "  To run test suite:"
echo "    source venv/bin/activate && pytest -q"
echo "============================================================================"
