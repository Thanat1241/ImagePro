"""Stable Diffusion image generation implementation."""

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any


_pipeline: Any | None = None
_pipeline_path: Path | None = None


def ratio_size(ratio: str) -> tuple[int, int]:
    return {
        "1:1": (512, 512),
        "4:3": (640, 480),
        "16:9": (768, 432),
        "9:16": (432, 768),
    }[ratio]


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

    try:
        import torch
        from diffusers import StableDiffusionPipeline
    except ImportError as error:
        raise RuntimeError("ยังไม่ได้ติดตั้ง torch/diffusers สำหรับ inference จริง") from error

    if _pipeline is None or _pipeline_path != model_path:
        report_progress(8, "กำลังโหลดโมเดล...")
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        _pipeline = StableDiffusionPipeline.from_single_file(str(model_path), torch_dtype=dtype)
        _pipeline = _pipeline.to("cuda" if torch.cuda.is_available() else "cpu")
        _pipeline_path = model_path

    width, height = ratio_size(ratio)
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_urls = []
    report_progress(30, "กำลังสร้างภาพ...")

    def report_step(pipeline: Any, step_index: int, _timestep: Any, callback_kwargs: dict[str, Any]) -> dict[str, Any]:
        total_steps = max(getattr(pipeline, "num_timesteps", 20), 1)
        progress = 30 + int(((step_index + 1) / total_steps) * 65)
        report_progress(
            min(progress, 95),
            f"กำลังสร้างภาพ... ขั้นตอน {step_index + 1}/{total_steps}",
        )
        return callback_kwargs

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