@echo off
setlocal enabledelayedexpansion

echo ============================================================================
echo   ShieldAI - Setup & Installation Script (Windows)
echo ============================================================================

:: 1. Check Python
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH. Please install Python 3.10+.
    exit /b 1
)

echo [*] Detected Python:
python --version

:: 2. Create Virtual Environment
if not exist "venv" (
    echo [*] Creating virtual environment 'venv'...
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        exit /b 1
    )
) else (
    echo [*] Virtual environment 'venv' already exists.
)

:: 3. Install Python Dependencies
echo [*] Installing backend dependencies from requirements.txt...
call venv\Scripts\python.exe -m pip install --upgrade pip
call venv\Scripts\pip.exe install -r backend\requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install backend dependencies.
    exit /b 1
)

:: 4. Install Frontend Dependencies
where npm >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [*] Installing frontend npm dependencies...
    cd frontend
    call npm install
    cd ..
) else (
    echo [WARN] npm not found. Skipping frontend package installation.
)

:: 5. Initialize & Seed Demo Database
echo [*] Initializing demo SQLite database...
call venv\Scripts\python.exe scripts\reset_demo.py

:: 6. Run System Doctor
echo [*] Running ShieldAI System Doctor...
call venv\Scripts\python.exe scripts\doctor.py

echo.
echo ============================================================================
echo   ShieldAI Setup Complete!
echo.
echo   To start the backend:
echo     venv\Scripts\python.exe backend\app.py
echo.
echo   To start the frontend:
echo     cd frontend ^&^& npm run dev
echo.
echo   To run the test suite:
echo     venv\Scripts\pytest.exe -q
echo ============================================================================

