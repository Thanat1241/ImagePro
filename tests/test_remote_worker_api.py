import asyncio
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

from backend import main
from database import store


class FakeRequest:
    async def body(self) -> bytes:
        return b"\x89PNG\r\n\x1a\nremote-image"


class RemoteWorkerApiTests(unittest.TestCase):
    def test_worker_claims_uploads_and_completes_job(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            with (
                patch.object(store, "DATABASE_PATH", temp_path / "jobs.sqlite3"),
                patch.object(main, "OUTPUTS_DIR", temp_path / "outputs"),
                patch.dict(os.environ, {"AI_WORKER_TOKEN": "test-secret"}),
            ):
                store.initialize_database()
                store.create_job({
                    "job_id": "job-1",
                    "prompt": "test prompt",
                    "model": "test model",
                    "model_file": "model.safetensors",
                    "ratio": "1:1",
                    "count": 1,
                    "cfg_scale": 7,
                    "base_url": "http://backend:8000",
                    "status": "queued",
                    "progress": 0,
                    "message": "queued",
                })

                job = main.claim_worker_job("Bearer test-secret")
                self.assertEqual(job["status"], "processing")

                main.report_worker_progress(
                    "job-1",
                    main.WorkerProgress(progress=50, message="rendering"),
                    "Bearer test-secret",
                )
                upload = asyncio.run(main.upload_worker_image(
                    "job-1",
                    "123456789.png",
                    FakeRequest(),
                    "Bearer test-secret",
                ))
                self.assertEqual(upload["url"], "http://backend:8000/outputs/123456789.png")

                main.complete_worker_job(
                    "job-1",
                    main.WorkerCompletion(
                        images=[main.GeneratedImage(
                            url=upload["url"],
                            prompt="test prompt",
                            model="test model",
                            ratio="1:1",
                        )],
                        model_path="models/model.safetensors",
                    ),
                    "Bearer test-secret",
                )

                completed = store.get_job("job-1")
                self.assertEqual(completed["status"], "completed")
                self.assertEqual(completed["images"][0]["url"], upload["url"])
                self.assertTrue((temp_path / "outputs" / "123456789.png").is_file())

    def test_worker_api_rejects_invalid_token(self):
        with patch.dict(os.environ, {"AI_WORKER_TOKEN": "test-secret"}):
            with self.assertRaises(HTTPException) as error:
                main.claim_worker_job("Bearer wrong-secret")
        self.assertEqual(error.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()