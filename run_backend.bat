@echo off
setlocal
set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

if not defined AI_WORKER_TOKEN (
    echo ERROR: Set AI_WORKER_TOKEN to the same secret used by the AI worker.
    echo Example in PowerShell: $env:AI_WORKER_TOKEN = "your-shared-secret"
    pause
    exit /b 1
)
if not defined AI_IMAGE_DATABASE set "AI_IMAGE_DATABASE=%PROJECT_ROOT%database\ai_image_studio.sqlite3"
if not defined AI_MODELS_DIR set "AI_MODELS_DIR=%PROJECT_ROOT%ai\models"
if not defined AI_OUTPUTS_DIR set "AI_OUTPUTS_DIR=%PROJECT_ROOT%ai\outputs"
if not defined BACKEND_HOST set "BACKEND_HOST=0.0.0.0"
if not defined BACKEND_PORT set "BACKEND_PORT=8000"

if exist "%PROJECT_ROOT%.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%PROJECT_ROOT%.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo.
echo Starting ImagePro backend...
"%PYTHON_EXE%" -m uvicorn backend.main:app --host "%BACKEND_HOST%" --port "%BACKEND_PORT%"

pause
