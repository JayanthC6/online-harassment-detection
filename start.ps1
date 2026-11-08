Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "       ShieldAI - Cyber Threat Intelligence Platform" -ForegroundColor Cyan
Write-Host "                Starting Backend & Frontend" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "`n[1/2] Launching Backend Server on http://127.0.0.1:5000 ..." -ForegroundColor Green
$backendProc = Start-Process -FilePath "$rootDir\venv\Scripts\python.exe" -ArgumentList "app.py" -WorkingDirectory "$rootDir\backend" -PassThru

Write-Host "[2/2] Launching Frontend Dev Server on http://localhost:5173 ..." -ForegroundColor Green
$frontendProc = Start-Process -FilePath "npm.cmd" -ArgumentList "run dev" -WorkingDirectory "$rootDir\frontend" -PassThru

Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host "ShieldAI is up and running!" -ForegroundColor Green
Write-Host "- Frontend Web App : http://localhost:5173" -ForegroundColor Yellow
Write-Host "- Backend API      : http://127.0.0.1:5000" -ForegroundColor Yellow
Write-Host "- Admin Credentials: admin / Sh13ldAI!Prod#2026 (or password123)" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Press Ctrl+C or close the terminal to stop."

try {
    Wait-Process -Id $backendProc.Id, $frontendProc.Id
} finally {
    Stop-Process -Id $backendProc.Id -ErrorAction SilentlyContinue
    Stop-Process -Id $frontendProc.Id -ErrorAction SilentlyContinue
}

