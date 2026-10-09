import os
import re
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import json
import shutil
import uuid
from typing import Literal

from fastapi import FastAPI, HTTPException, Request as FastAPIRequest
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


app = FastAPI(title="AI Image Studio Backend", version="1.0.0")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL")
MODELS_DIR = Path(__file__).resolve().parent / "models"
OUTPUTS_DIR = Path(__file__).resolve().parent / "outputs"
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

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "ai-image-backend"}


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
        if not model_path.is_file():
            raise HTTPException(status_code=404, detail="ไม่พบโมเดลใน backend/models")
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

    raise HTTPException(status_code=400, detail="กรุณาดาวน์โหลดและเลือกโมเดลใน backend/models ก่อนสร้างภาพ")


@app.get("/api/generate/{job_id}")
def generation_status(job_id: str):
    job = store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="ไม่พบงานสร้างภาพ")
    return job


@app.get("/api/history")
def generation_history(limit: int = 50):
    return {"jobs": store.list_jobs(limit)}