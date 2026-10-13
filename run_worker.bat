@echo off
setlocal
set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

if not defined AI_BACKEND_URL set "AI_BACKEND_URL=http://127.0.0.1:8000"
if not defined AI_WORKER_TOKEN (
    echo ERROR: Set AI_WORKER_TOKEN to the same secret used by the backend.
    echo Example in PowerShell: $env:AI_WORKER_TOKEN = "your-shared-secret"
    pause
    exit /b 1
)
if not defined AI_MODELS_DIR set "AI_MODELS_DIR=%PROJECT_ROOT%ai\models"
if not defined AI_OUTPUTS_DIR set "AI_OUTPUTS_DIR=%PROJECT_ROOT%ai\outputs"

if exist "%PROJECT_ROOT%.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%PROJECT_ROOT%.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo.
echo Starting AI worker...
"%PYTHON_EXE%" ai\worker.py

pause
