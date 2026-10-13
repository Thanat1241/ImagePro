@echo off
setlocal
set "PROJECT_ROOT=%~dp0"
if not defined AI_WORKER_TOKEN set "AI_WORKER_TOKEN=dev-secret"
if not defined AI_BACKEND_URL set "AI_BACKEND_URL=http://127.0.0.1:8000"

start "ImagePro Backend" cmd /k "%PROJECT_ROOT%run_backend.bat"
ping -n 2 127.0.0.1 >nul
start "ImagePro Frontend" cmd /k "%PROJECT_ROOT%run_frontend.bat"
ping -n 2 127.0.0.1 >nul
start "ImagePro Worker" cmd /k "%PROJECT_ROOT%run_worker.bat"

echo All ImagePro services started.
echo Open: http://127.0.0.1:5500
pause
