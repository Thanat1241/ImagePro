import os
import re
import sys
import hmac
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import json
import shutil
import uuid
from typing import Literal

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, Header, HTTPException, Request as FastAPIRequest, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from database import store


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=500)
    model: str = "meinamix_v12Final.safetensors"
    ratio: Literal["1:1", "4:3", "16:9", "9:16"] = "1:1"
    count: int = Field(default=1, ge=1, le=4)
    cfg_scale: float = Field(default=7, ge=1, le=20)
    model_file: str | None = None


class DownloadModelRequest(BaseModel):
    download_url: str
    filename: str | None = None
    civitai_model_id: int | None = None
    civitai_version_id: int | None = None


class GeneratedImage(BaseModel):
    url: str
    prompt: str
    model: str
    ratio: str


class WorkerProgress(BaseModel):
    progress: int = Field(ge=0, le=99)
    message: str = Field(max_length=500)


class WorkerCompletion(BaseModel):
    images: list[GeneratedImage]
    model_path: str
    engine: str = "diffusers"


class WorkerFailure(BaseModel):
    message: str = Field(min_length=1, max_length=1000)




def resolve_shared_path(env_name: str, default_path: Path) -> Path:
    configured = os.getenv(env_name)
    if not configured:
        return default_path

    candidate = Path(configured).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate


app = FastAPI(title="AI Image Studio Backend", version="1.0.0")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
MODELS_DIR = resolve_shared_path("AI_MODELS_DIR", PROJECT_ROOT / "ai" / "models")
OUTPUTS_DIR = resolve_shared_path("AI_OUTPUTS_DIR", PROJECT_ROOT / "ai" / "outputs")
MODELS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_MODEL_EXTENSIONS = {".safetensors", ".ckpt", ".gguf", ".pt", ".pth"}
DEFAULT_MODEL_FILE = "meinamix_v12Final.safetensors"
store.initialize_database()
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://[^/]+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/outputs", StaticFiles(directory=OUTPUTS_DIR), name="outputs")


@app.get("/")
def root_status():
    return {
        "status": "ok",
        "service": "ai-image-backend",
        "message": "This is the API backend. Open the frontend on port 5500, e.g. http://<HOST_IP>:5500",
        "health_url": "/api/health",
        "frontend_url": "http://<HOST_IP>:5500",
    }

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "ai-image-backend"}


def require_worker_token(authorization: str | None) -> None:
    expected_token = os.getenv("AI_WORKER_TOKEN", "")
    if not expected_token:
        raise HTTPException(status_code=503, detail="AI worker is not configured")
    supplied_token = authorization.removeprefix("Bearer ") if authorization else ""
    if not hmac.compare_digest(supplied_token, expected_token):
        raise HTTPException(status_code=401, detail="Invalid worker token")


def require_processing_job(job_id: str) -> dict:
    job = store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="ไม่พบงานสร้างภาพ")
    if job["status"] != "processing":
        raise HTTPException(status_code=409, detail="งานนี้ไม่ได้อยู่ในสถานะกำลังประมวลผล")
    return job


@app.post("/api/worker/jobs/claim")
def claim_worker_job(authorization: str | None = Header(default=None)):
    require_worker_token(authorization)
    job = store.claim_next_job()
    if job is None:
        return Response(status_code=204)
    return job


@app.post("/api/worker/jobs/{job_id}/progress")
def report_worker_progress(job_id: str, update: WorkerProgress, authorization: str | None = Header(default=None)):
    require_worker_token(authorization)
    require_processing_job(job_id)
    store.update_job(job_id, progress=update.progress, message=update.message)
    return {"status": "ok"}


@app.put("/api/worker/jobs/{job_id}/images/{filename}")
async def upload_worker_image(job_id: str, filename: str, http_request: FastAPIRequest, authorization: str | None = Header(default=None)):
    require_worker_token(authorization)
    job = require_processing_job(job_id)
    if not re.fullmatch(r"[0-9]+\.png", filename):
        raise HTTPException(status_code=400, detail="ชื่อไฟล์ภาพไม่ถูกต้อง")

    image_data = await http_request.body()
    if len(image_data) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="ไฟล์ภาพมีขนาดใหญ่เกินไป")
    if not image_data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise HTTPException(status_code=415, detail="รองรับเฉพาะไฟล์ PNG")

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    destination = OUTPUTS_DIR / filename
    destination.write_bytes(image_data)
    return {"url": f"{job['base_url'].rstrip('/')}/outputs/{filename}"}


@app.post("/api/worker/jobs/{job_id}/complete")
def complete_worker_job(job_id: str, result: WorkerCompletion, authorization: str | None = Header(default=None)):
    require_worker_token(authorization)
    require_processing_job(job_id)
    store.update_job(
        job_id,
        status="completed",
        progress=100,
        message="สร้างภาพเสร็จแล้ว",
        images=[image.model_dump() for image in result.images],
        model_path=result.model_path,
        engine=result.engine,
    )
    return {"status": "completed"}


@app.post("/api/worker/jobs/{job_id}/fail")
def fail_worker_job(job_id: str, failure: WorkerFailure, authorization: str | None = Header(default=None)):
    require_worker_token(authorization)
    require_processing_job(job_id)
    store.update_job(job_id, status="failed", progress=0, message=failure.message)
    return {"status": "failed"}


def safe_filename(filename: str) -> str:
    cleaned = Path(filename).name
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "_", cleaned)
    if not cleaned or Path(cleaned).suffix.lower() not in ALLOWED_MODEL_EXTENSIONS:
        raise HTTPException(status_code=400, detail="รองรับเฉพาะไฟล์โมเดล .safetensors, .ckpt, .gguf, .pt หรือ .pth")
    return cleaned


@app.get("/api/models")
def list_models():
    files = []
    for path in sorted(MODELS_DIR.iterdir()):
        if path.is_file() and path.suffix.lower() in ALLOWED_MODEL_EXTENSIONS:
            files.append({"filename": path.name, "size_bytes": path.stat().st_size})
    return {"directory": str(MODELS_DIR), "models": files}


@app.get("/api/models/search")
def search_civitai_models(query: str = "", limit: int = 20):
    params = f"?query={query}&limit={min(max(limit, 1), 100)}" if query else f"?limit={min(max(limit, 1), 100)}"
    request = Request(
        f"https://civitai.com/api/v1/models{params}",
        headers={"User-Agent": "AIImageStudio/1.0"},
    )
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"เรียก Civitai ไม่สำเร็จ: {error}") from error
    return {"items": payload.get("items", []), "metadata": payload.get("metadata", {})}


@app.post("/api/models/download")
def download_model(request: DownloadModelRequest):
    parsed_url = urlparse(request.download_url)
    if parsed_url.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="download_url ต้องเป็น http หรือ https")
    source_name = Path(parsed_url.path).name or "model.safetensors"
    filename = safe_filename(request.filename or source_name)
    destination = MODELS_DIR / filename
    if destination.exists():
        return {"status": "exists", "filename": filename, "path": str(destination)}

    headers = {"User-Agent": "AIImageStudio/1.0"}
    api_key = os.getenv("CIVITAI_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        with urlopen(Request(request.download_url, headers=headers), timeout=30) as source, destination.open("wb") as target:
            shutil.copyfileobj(source, target, length=1024 * 1024)
    except Exception as error:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=502, detail=f"ดาวน์โหลดโมเดลไม่สำเร็จ: {error}") from error
    return {"status": "downloaded", "filename": filename, "path": str(destination)}


@app.post("/api/generate")
def generate_image(request: GenerateRequest, http_request: FastAPIRequest):
    selected_model_file = request.model_file or DEFAULT_MODEL_FILE
    if selected_model_file:
        model_file = safe_filename(selected_model_file)
        model_path = MODELS_DIR / model_file
        # Model files may live on the AI machine instead of the backend machine.
        # The actual validation happens in the worker when it claims the job.
    else:
        model_path = None
    if model_path:
        job_id = uuid.uuid4().hex
        base_url = (PUBLIC_BASE_URL or str(http_request.base_url)).rstrip("/")
        store.create_job({
            "job_id": job_id,
            "prompt": request.prompt,
            "model": request.model,
            "model_file": model_path.name,
            "ratio": request.ratio,
            "count": request.count,
            "cfg_scale": request.cfg_scale,
            "base_url": base_url,
            "status": "queued",
            "progress": 0,
            "message": "รอ AI worker รับงาน...",
        })
        return {"job_id": job_id, "status": "queued"}

    raise HTTPException(status_code=400, detail="กรุณาเลือกไฟล์โมเดลที่ถูกต้องก่อนสร้างภาพ")


@app.get("/api/generate/{job_id}")
def generation_status(job_id: str):
    job = store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="ไม่พบงานสร้างภาพ")
    return job


@app.get("/api/history")
def generation_history(limit: int = 50):
    return {"jobs": store.list_jobs(limit)}
