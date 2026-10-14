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

# ตั้งค่าเริ่มต้นสำหรับ Hugging Face เพื่อหลีกเลี่ยงปัญหา symlink บน Windows
# ช่วยให้การโหลดโมเดลจาก cache หรือ filesystem ทำงานได้เสถียรขึ้น
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

# กำหนด root ของโปรเจกต์ เพื่อให้ import โมดูลภายใน ai/ ได้ถูกต้อง
# และให้ worker ใช้ path ถูกต้องแม้รันจากตำแหน่งต่าง ๆ
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# นำฟังก์ชันการสร้างภาพจาก ai.image_generator มาใช้งาน
from ai.image_generator import generate_images


# สร้าง path ที่สามารถ override ได้จาก environment variable
# ใช้สำหรับโฟลเดอร์โมเดลและ output ที่อาจอยู่ต่างที่จากค่า default
# ถ้าไม่ได้ตั้งค่า env จะใช้ค่า default ตามโปรเจกต์
#
# ตัวอย่าง: AI_MODELS_DIR หรือ AI_OUTPUTS_DIR
# หาก env ถูกกำหนดเป็น relative path จะเปลี่ยนให้เป็น absolute path ภายใน root
# เพื่อให้ worker รันได้แม้เปิดโปรเจกต์จาก directory อื่น
def resolve_shared_path(env_name: str, default_path: Path) -> Path:
    configured = os.getenv(env_name)
    if not configured:
        return default_path

    candidate = Path(configured).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate


# กำหนด path หลักที่ worker ใช้
# BACKEND_DIR: ไว้สำหรับโฟลเดอร์ backend ของโปรเจกต์ (ปัจจุบันไม่ใช้ตรง ๆ แต่เตรียมไว้)
# MODELS_DIR: โฟลเดอร์ที่เก็บโมเดลสำหรับสร้างภาพ
# OUTPUTS_DIR: โฟลเดอร์ที่เก็บไฟล์ภาพที่สร้างเสร็จ
# BACKEND_URL: URL ของ backend API ที่ worker จะคุยด้วย
# WORKER_TOKEN: โทเค็นสำหรับยืนยันตัวตนตาม JWT/Bearer token
BACKEND_DIR = PROJECT_ROOT / "backend"
MODELS_DIR = resolve_shared_path("AI_MODELS_DIR", PROJECT_ROOT / "ai" / "models")
OUTPUTS_DIR = resolve_shared_path("AI_OUTPUTS_DIR", PROJECT_ROOT / "ai" / "outputs")
BACKEND_URL = os.getenv("AI_BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
WORKER_TOKEN = os.getenv("AI_WORKER_TOKEN", "")
POLL_INTERVAL_SECONDS = 1
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# ฟังก์ชันสำหรับส่ง request ไปที่ backend
# ใช้ HTTP method ที่ระบุ เช่น POST / PUT
# ถ้า payload ไม่ใช่ None จะส่งเป็น JSON
# ถ้า body ไม่ใช่ None จะส่งเป็น binary (สำหรับอัปโหลดไฟล์ภาพ)
# มักใช้ใน workflow:
# - claim job
# - report progress
# - upload image
# - mark complete/fail
#
# การออกแบบนี้ทำให้ code หลักเคลียร์ขึ้น เพราะ worker ไม่ต้องเขียน HTTP logic ซ้ำซ้ำ
#
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


# process_job คือหัวใจของการทำงานจริง
# เมื่อ backend ส่ง job มาให้ worker แล้ว worker จะทำสิ่งต่อไปนี้:
# 1) ตรวจว่ามี model file ที่ต้องใช้หรือไม่
# 2) ดึง prompt/ratio/count/cfg_scale จาก job
# 3) เรียก generate_images() เพื่อสร้างภาพหลายรูป
# 4) อัปโหลดภาพที่สร้างได้ไปยัง backend
# 5) แจ้ง backend ว่า job เสร็จแล้ว
#
# callback report_progress ถูกส่งเข้าไปใน generator เพื่อให้ backend ได้รับ update
# ในระหว่างที่ generator กำลัง render เราสามารถแจ้ง progress ให้ UI หรือ dashboard ดูได้
# 
def process_job(job: dict[str, Any]) -> None:
    job_id = job["job_id"]
    model_path = MODELS_DIR / Path(job["model_file"]).name

    try:
        # ตรวจว่าสามารถใช้ model file นี้ได้หรือไม่
        # ถ้าไม่มี จะยก exception ทันที แล้วเข้าสู่ส่วน catch เพื่อแจ้ง fail ให้ backend
        if not model_path.is_file():
            raise FileNotFoundError(f"ไม่พบโมเดลในโฟลเดอร์ของ AI worker: {model_path.name}")

        # เรียกใช้ generator จริงเพื่อสร้างภาพ
        # arguments ต่าง ๆ มาจากข้อมูล job ที่ backend จัดสรรมาให้
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

        # หลังจาก generate_images สำเร็จ จะมี URL ของภาพที่ถูกสร้างแล้ว
        # loop นี้เอา URL มาทำการ upload ไปยัง backend
        # โดยแปลงชื่อไฟล์ให้ปลอดภัยและอ่าน binary จาก OUTPUTS_DIR แล้วส่งไป PUT
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

        # เมื่อทุกภาพ upload เสร็จแล้ว ให้ backend ทราบว่า job สำเร็จและส่งผลลัพธ์กลับ
        backend_request(
            "POST",
            f"/api/worker/jobs/{job_id}/complete",
            {"images": images, "model_path": str(model_path), "engine": "diffusers"},
        )
        logger.info("Generation job %s completed", job_id)
    except Exception as error:
        # ถ้าเกิด exception ใด ๆ ตั้งแต่ model not found, generate fail, upload fail
        # ให้ log อย่างละเอียด แล้วส่ง status fail กลับให้ backend
        logger.exception("Generation job %s failed", job_id)
        try:
            backend_request(
                "POST",
                f"/api/worker/jobs/{job_id}/fail",
                {"message": str(error)[:1000]},
            )
        except Exception:
            logger.exception("Could not report failure for job %s", job_id)


# run_worker เป็น loop หลักของ worker
# โดยจะทำหน้าที่คอย poll backend อย่างต่อเนื่อง เพื่อ claim งานใหม่
# ถ้า backend ไม่มีงาน จะ sleep 1 วินาที แล้ววนต่อ
# ถ้ามีงานก็เรียก process_job(job) เพื่อทำงานต่อ
# ทำหน้าที่เหมือน 'consumer' ของ queue
#
def run_worker() -> None:
    # ตรวจสอบความพร้อมก่อนเริ่มทำงาน
    if not WORKER_TOKEN:
        raise RuntimeError("ตั้งค่า AI_WORKER_TOKEN ให้ตรงกับ backend ก่อนเริ่ม worker")
    if not BACKEND_URL.startswith(("http://", "https://")):
        raise RuntimeError("AI_BACKEND_URL ต้องเริ่มต้นด้วย http:// หรือ https://")

    logger.info("AI worker is polling %s", BACKEND_URL)
    while True:
        try:
            # พยายาม claim job จาก backend แบบ polling
            # ในกรณีที่ backend ว่างหรือไม่มีงาน จะได้ response เป็น empty/None
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


# จุดเริ่มต้นของโปรแกรม
# ถ้ายังไม่ตั้งค่า token หรือ URL ถูกต้อง โปรแกรมจะหยุดทันที
# KeyboardInterrupt ใช้จัดการเมื่อผู้ใช้กด Ctrl+C เพื่อให้ process หยุดแบบสวยงาม
if __name__ == "__main__":
    try:
        run_worker()
    except KeyboardInterrupt:
        logger.info("AI worker stopped")
