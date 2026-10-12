import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path


def wait_for_url(url: str, timeout: float = 20.0) -> str:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                return response.read().decode('utf-8', 'ignore')
        except Exception as exc:  # pragma: no cover - wait loop
            last_error = exc
            time.sleep(0.5)
    raise RuntimeError(f'URL did not respond in time: {url} (last error: {last_error})')


def main() -> None:
    base = Path(__file__).resolve().parents[1]
    work = Path(tempfile.mkdtemp(prefix='imagepro-'))
    model_dir = work / 'models'
    output_dir = work / 'outputs'
    db_path = work / 'ai_image_studio.sqlite3'

    env = os.environ.copy()
    env['AI_IMAGE_DATABASE'] = str(db_path)
    env['AI_MODELS_DIR'] = str(model_dir)
    env['AI_OUTPUTS_DIR'] = str(output_dir)
    env['PUBLIC_BASE_URL'] = 'http://127.0.0.1:8000'

    backend = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', '8000'],
        cwd=str(base),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    frontend = subprocess.Popen(
        [sys.executable, 'frontend/ai_image_frontend.py', '--api-url', 'http://127.0.0.1:8000', '--host', '127.0.0.1', '--port', '5500'],
        cwd=str(base),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        health = wait_for_url('http://127.0.0.1:8000/api/health')
        page = wait_for_url('http://127.0.0.1:5500/')

        if '"status":"ok"' not in health:
            raise RuntimeError(f'Unexpected backend health payload: {health}')
        if 'IMAGE STUDIO' not in page:
            raise RuntimeError('Frontend page did not render the expected content')

        print('HEALTH_OK', health)
        print('FRONTEND_OK', 'IMAGE STUDIO' in page)
        print('MODEL_DIR', model_dir)
        print('OUTPUT_DIR', output_dir)
        print('DB_PATH', db_path)
    finally:
        for proc in (backend, frontend):
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)


if __name__ == '__main__':
    main()
