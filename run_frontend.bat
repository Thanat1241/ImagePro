@echo off
setlocal
set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

if not defined AI_BACKEND_URL set "AI_BACKEND_URL=http://127.0.0.1:8000"
if not defined FRONTEND_HOST set "FRONTEND_HOST=0.0.0.0"
if not defined FRONTEND_PORT set "FRONTEND_PORT=5500"

if exist "%PROJECT_ROOT%.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%PROJECT_ROOT%.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo.
echo Starting ImagePro frontend...
"%PYTHON_EXE%" frontend\ai_image_frontend.py --api-url "%AI_BACKEND_URL%" --host "%FRONTEND_HOST%" --port "%FRONTEND_PORT%"

pause
