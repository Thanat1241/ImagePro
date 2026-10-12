import importlib
import os
import tempfile
import unittest
from pathlib import Path


class RemoteConfigTests(unittest.TestCase):
    def test_backend_and_worker_use_shared_env_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            models_dir = Path(temp_dir) / "shared" / "models"
            outputs_dir = Path(temp_dir) / "shared" / "outputs"

            old_models = os.environ.get("AI_MODELS_DIR")
            old_outputs = os.environ.get("AI_OUTPUTS_DIR")
            os.environ["AI_MODELS_DIR"] = str(models_dir)
            os.environ["AI_OUTPUTS_DIR"] = str(outputs_dir)

            try:
                import ai.worker as worker_module
                import backend.main as backend_module

                importlib.reload(worker_module)
                importlib.reload(backend_module)

                self.assertEqual(worker_module.MODELS_DIR, models_dir)
                self.assertEqual(worker_module.OUTPUTS_DIR, outputs_dir)
                self.assertEqual(backend_module.MODELS_DIR, models_dir)
                self.assertEqual(backend_module.OUTPUTS_DIR, outputs_dir)
            finally:
                if old_models is None:
                    os.environ.pop("AI_MODELS_DIR", None)
                else:
                    os.environ["AI_MODELS_DIR"] = old_models

                if old_outputs is None:
                    os.environ.pop("AI_OUTPUTS_DIR", None)
                else:
                    os.environ["AI_OUTPUTS_DIR"] = old_outputs


if __name__ == "__main__":
    unittest.main()
