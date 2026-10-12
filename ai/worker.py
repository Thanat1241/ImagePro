"""Background worker that claims generation jobs from the SQLite queue."""

import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.image_generator import generate_images
from database import store




def resolve_shared_path(env_name: str, default_path: Path) -> Path:
    configured = os.getenv(env_name)
    if not configured:
        return default_path

    candidate = Path(configured).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate


BACKEND_DIR = PROJECT_ROOT / "backend"
MODELS_DIR = resolve_shared_path("AI_MODELS_DIR", BACKEND_DIR / "models")
OUTPUTS_DIR = resolve_shared_path("AI_OUTPUTS_DIR", BACKEND_DIR / "outputs")
POLL_INTERVAL_SECONDS = 1
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def process_job(job: dict[str, Any]) -> None:
    job_id = job["job_id"]
    model_path = MODELS_DIR / Path(job["model_file"]).name

    try:
        if not model_path.is_file():
            raise FileNotFoundError(f"ไม่พบโมเดลใน shared model directory: {model_path.name}")

        generated_urls = generate_images(
            model_path,
            prompt=job["prompt"],
            ratio=job["ratio"],
            count=job["count"],
            cfg_scale=job["cfg_scale"],
            output_dir=OUTPUTS_DIR,
            base_url=job["base_url"],
            report_progress=lambda progress, message: store.update_job(
                job_id,
                progress=progress,
                message=message,
            ),
        )
        images = [
            {
                "url": url,
                "prompt": job["prompt"],
                "model": job["model"],
                "ratio": job["ratio"],
            }
            for url in generated_urls
        ]
        store.update_job(
            job_id,
            status="completed",
            progress=100,
            message="สร้างภาพเสร็จแล้ว",
            images=images,
            model_path=str(model_path),
            engine="diffusers",
        )
        logger.info("Generation job %s completed", job_id)
    except Exception as error:
        logger.exception("Generation job %s failed", job_id)
        store.update_job(job_id, status="failed", progress=0, message=str(error))


def run_worker() -> None:
    store.initialize_database()
    logger.info("AI worker is running; polling the database queue")
    while True:
        job = store.claim_next_job()
        if job is None:
            time.sleep(POLL_INTERVAL_SECONDS)
            continue
        logger.info("Processing generation job %s", job["job_id"])
        process_job(job)


if __name__ == "__main__":
    try:
        run_worker()
    except KeyboardInterrupt:
        logger.info("AI worker stopped")