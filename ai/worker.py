"""Background worker that claims generation jobs from the backend API."""

import logging
import os
import sys
import time
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.image_generator import generate_images


def resolve_shared_path(env_name: str, default_path: Path) -> Path:
    configured = os.getenv(env_name)
    if not configured:
        return default_path

    candidate = Path(configured).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate


BACKEND_DIR = PROJECT_ROOT / "backend"
MODELS_DIR = resolve_shared_path("AI_MODELS_DIR", PROJECT_ROOT / "ai" / "models")
OUTPUTS_DIR = resolve_shared_path("AI_OUTPUTS_DIR", PROJECT_ROOT / "ai" / "outputs")
BACKEND_URL = os.getenv("AI_BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
WORKER_TOKEN = os.getenv("AI_WORKER_TOKEN", "")
POLL_INTERVAL_SECONDS = 1
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def backend_request(method: str, path: str, payload: dict[str, Any] | None = None, body: bytes | None = None) -> Any:
    headers = {"Authorization": f"Bearer {WORKER_TOKEN}"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif body is not None:
        headers["Content-Type"] = "image/png"

    request = Request(f"{BACKEND_URL}{path}", data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=30) as response:
            response_body = response.read()
            return json.loads(response_body) if response_body else None
    except HTTPError as error:
        detail = error.read().decode("utf-8", "replace")
        raise RuntimeError(f"Backend ตอบกลับ HTTP {error.code}: {detail}") from error
    except URLError as error:
        raise RuntimeError(f"เชื่อมต่อ Backend ไม่ได้: {error.reason}") from error


def process_job(job: dict[str, Any]) -> None:
    job_id = job["job_id"]
    model_path = MODELS_DIR / Path(job["model_file"]).name

    try:
        if not model_path.is_file():
            raise FileNotFoundError(f"ไม่พบโมเดลในโฟลเดอร์ของ AI worker: {model_path.name}")

        generated_urls = generate_images(
            model_path,
            prompt=job["prompt"],
            ratio=job["ratio"],
            count=job["count"],
            cfg_scale=job["cfg_scale"],
            output_dir=OUTPUTS_DIR,
            base_url=job["base_url"],
            report_progress=lambda progress, message: backend_request(
                "POST",
                f"/api/worker/jobs/{job_id}/progress",
                {"progress": progress, "message": message},
            ),
        )
        images = []
        for generated_url in generated_urls:
            filename = Path(urlparse(generated_url).path).name
            image_path = OUTPUTS_DIR / filename
            uploaded = backend_request(
                "PUT",
                f"/api/worker/jobs/{job_id}/images/{quote(filename)}",
                body=image_path.read_bytes(),
            )
            images.append({
                "url": uploaded["url"],
                "prompt": job["prompt"],
                "model": job["model"],
                "ratio": job["ratio"],
            })
        backend_request(
            "POST",
            f"/api/worker/jobs/{job_id}/complete",
            {"images": images, "model_path": str(model_path), "engine": "diffusers"},
        )
        logger.info("Generation job %s completed", job_id)
    except Exception as error:
        logger.exception("Generation job %s failed", job_id)
        try:
            backend_request(
                "POST",
                f"/api/worker/jobs/{job_id}/fail",
                {"message": str(error)[:1000]},
            )
        except Exception:
            logger.exception("Could not report failure for job %s", job_id)


def run_worker() -> None:
    if not WORKER_TOKEN:
        raise RuntimeError("ตั้งค่า AI_WORKER_TOKEN ให้ตรงกับ backend ก่อนเริ่ม worker")
    if not BACKEND_URL.startswith(("http://", "https://")):
        raise RuntimeError("AI_BACKEND_URL ต้องเริ่มต้นด้วย http:// หรือ https://")
    logger.info("AI worker is polling %s", BACKEND_URL)
    while True:
        try:
            job = backend_request("POST", "/api/worker/jobs/claim")
        except Exception:
            logger.exception("Could not claim a job from the backend")
            time.sleep(POLL_INTERVAL_SECONDS)
            continue
        if not job:
            time.sleep(POLL_INTERVAL_SECONDS)
            continue
        logger.info("Processing generation job %s", job["job_id"])
        process_job(job)


if __name__ == "__main__":
    try:
        run_worker()
    except KeyboardInterrupt:
        logger.info("AI worker stopped")
