"""Stable Diffusion image generation implementation."""

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any


# Cache pipeline ไว้แบบ global เพื่อไม่ต้องโหลดโมเดลซ้ำทุกครั้ง
# _pipeline_path ใช้ติดตามว่าโมเดลปัจจุบันตรงกับ model ที่ต้องใช้หรือไม่
_pipeline: Any | None = None
_pipeline_path: Path | None = None


# map ค่าอัตราส่วนภาพให้เป็นขนาด pixel ที่เหมาะสมกับ Stable Diffusion
# ตัวอย่าง ratio = "16:9" จะได้ความกว้าง 768 x สูง 432
# โดยปกติจะใช้เป็นขนาดที่ไม่เกินพอสมควรเพื่อประหยัด VRAM/เวลา
#
def ratio_size(ratio: str) -> tuple[int, int]:
    return {
        "1:1": (512, 512),
        "4:3": (640, 480),
        "16:9": (768, 432),
        "9:16": (432, 768),
    }[ratio]


# ฟังก์ชันหลักที่ใช้สร้างภาพหลายรูปตาม prompt
# ตัวแปรสำคัญ:
# - model_path: path ของโมเดล Stable Diffusion ที่ต้องใช้
# - prompt: ข้อความสั่งให้สร้างภาพ
# - ratio: อัตราส่วนภาพ เช่น 1:1, 16:9
# - count: จำนวนภาพที่ต้องการสร้าง
# - cfg_scale: ค่าความเข้มของ prompt (classifier-free guidance scale)
# - output_dir: โฟลเดอร์สำหรับบันทึกภาพ
# - base_url: base URL ของ backend/frontend สำหรับสร้าง URL ไปให้ client อ้างอิง
# - report_progress: callback สำหรับส่งความคืบหน้าไป backend ให้ UI อัปเดต
#
# คืนค่าเป็น list ของ URL แบบเต็ม เช่น http://127.0.0.1:8000/outputs/xxx.png
#
def generate_images(
    model_path: Path,
    *,
    prompt: str,
    ratio: str,
    count: int,
    cfg_scale: float,
    output_dir: Path,
    base_url: str,
    report_progress: Callable[[int, str], None],
) -> list[str]:
    global _pipeline, _pipeline_path

    # ตรวจว่ามี dependency ที่จำเป็นสำหรับ inference จริงหรือยัง
    # ถ้าไม่มี torch หรือ diffusers จะยก exception แจ้งให้ติดตั้งก่อนใช้งาน
    try:
        import torch
        from diffusers import StableDiffusionPipeline
    except ImportError as error:
        raise RuntimeError("ยังไม่ได้ติดตั้ง torch/diffusers สำหรับ inference จริง") from error

    # ถ้ายังไม่มี pipeline หรือโมเดลที่เลือกต่างจาก pipeline ปัจจุบัน
    # ให้โหลดโมเดลใหม่โดยใช้ from_single_file()
    # dtype จะใช้ float16 ถ้ามี GPU หรือ float32 ถ้าเป็น CPU
    # หลังจากโหลดเสร็จจะย้าย pipeline ไปยัง device ที่เหมาะสม (cuda / cpu)
    if _pipeline is None or _pipeline_path != model_path:
        report_progress(8, "กำลังโหลดโมเดล...")
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        _pipeline = StableDiffusionPipeline.from_single_file(str(model_path), torch_dtype=dtype)
        _pipeline = _pipeline.to("cuda" if torch.cuda.is_available() else "cpu")
        _pipeline_path = model_path

    # คำนวณขนาดภาพตาม ratio ที่กรอกเข้ามา
    width, height = ratio_size(ratio)

    # สร้างโฟลเดอร์ output หากยังไม่มี
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_urls = []
    report_progress(30, "กำลังสร้างภาพ...")

    # callback แบบ per-step สำหรับติดตามความคืบหน้าของการ denoise
    # pipeline จะเรียก callback นี้ทุก step เพื่อให้ UI รู้ว่า image still generating
    # progress จะคำนวณจาก step_index / num_timesteps และส่งกลับเป็นเปอร์เซ็นต์
    #
    # callback must return callback_kwargs เพื่อให้ diffusers ดำเนินการต่อได้
    def report_step(pipeline: Any, step_index: int, _timestep: Any, callback_kwargs: dict[str, Any]) -> dict[str, Any]:
        total_steps = max(getattr(pipeline, "num_timesteps", 20), 1)
        progress = 30 + int(((step_index + 1) / total_steps) * 65)
        report_progress(
            min(progress, 95),
            f"กำลังสร้างภาพ... ขั้นตอน {step_index + 1}/{total_steps}",
        )
        return callback_kwargs

    # loop สร้างภาพตามจำนวน count
    # แม้จะใช้ same model แต่แต่ละภาพอาจใช้ prompt เดียวกัน แล้ว save เป็นไฟล์ png
    # ชื่อไฟล์ใช้ time.time_ns() เพื่อป้องกันชื่อซ้ำและง่ายต่อการระบุไฟล์แต่ละอัน
    for image_index in range(count):
        image = _pipeline(
            prompt,
            guidance_scale=cfg_scale,
            width=width,
            height=height,
            callback_on_step_end=report_step,
        ).images[0]
        filename = f"{time.time_ns()}.png"
        image.save(output_dir / filename)
        generated_urls.append(f"{base_url.rstrip('/')}/outputs/{filename}")
        report_progress(95, f"บันทึกภาพ {image_index + 1}/{count}")

    return generated_urls