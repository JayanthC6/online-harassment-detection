@echo off
echo ========================================================
echo        ShieldAI - Cyber Threat Intelligence Platform
echo                 Starting Backend & Frontend
echo ========================================================

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo [1/2] Launching Backend Server on http://127.0.0.1:5000 ...
start "ShieldAI Backend" cmd /k "cd backend && ..\venv\Scripts\python.exe app.py"

echo [2/2] Launching Frontend Dev Server on http://localhost:5173 ...
start "ShieldAI Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================================
echo ShieldAI is starting!
echo - Web App: http://localhost:5173
echo - Backend API: http://127.0.0.1:5000
echo - Admin Credentials: admin / Sh13ldAI!Prod#2026 (or password123)
echo ========================================================

