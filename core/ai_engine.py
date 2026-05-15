"""
AIEngine — modular, mode-aware image upscaling.

LOW mode      → Real-ESRGAN x2plus ONNX  (CPU, ~65 MB, good quality)
BALANCED mode → Real-ESRGAN x4plus ONNX  (CPU, ~65 MB, 4x upscale)
ULTRA mode    → same as balanced (GPU path reserved for future)

If the ONNX model is unavailable (download failed / no internet),
the engine falls back to high-quality Lanczos interpolation automatically.
"""

import logging
import os
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

from utils.constants import SUPPORTED_AI_MODES, DEFAULT_AI_MODE, DEFAULT_SCALE_FACTOR

logger = logging.getLogger("uic_app")

# ── Model registry ────────────────────────────────────────────────────────────
# (filename, huggingface_url, native_scale)
_MODELS = {
    "low": (
        "RealESRGAN_x2plus.onnx",
        "https://huggingface.co/UmeAiRT/ComfyUI-Auto_installer/resolve/ac2e37c9404cd8fb509d2d215d568062c196dbdd/models/onnx/RealESRGAN_x4.onnx",
        2,
    ),
    "balanced": (
        "RealESRGAN_x4plus.onnx",
        "https://huggingface.co/UmeAiRT/ComfyUI-Auto_installer/resolve/ac2e37c9404cd8fb509d2d215d568062c196dbdd/models/onnx/RealESRGAN_x4.onnx",
        4,
    ),
}


class AIEngine:

    MODES = tuple(SUPPORTED_AI_MODES)

    def __init__(self, mode: str = DEFAULT_AI_MODE, model_manager=None):
        self.mode = mode if mode in self.MODES else DEFAULT_AI_MODE
        self.model_manager = model_manager
        self._sessions: dict = {}
        logger.debug("AIEngine initialised in '%s' mode.", self.mode)

    # ── Mode management ───────────────────────────────────────────────────────

    def set_mode(self, mode: str) -> None:
        if mode in self.MODES:
            self.mode = mode
            logger.info("AI mode changed to '%s'.", mode)
        else:
            logger.warning("Unknown AI mode '%s' — keeping '%s'.", mode, self.mode)

    def get_mode(self) -> str:
        return self.mode

    def is_available(self) -> bool:
        return True

    # ── Public upscale API ────────────────────────────────────────────────────

    def upscale(self, image: Image.Image, scale_factor: float = DEFAULT_SCALE_FACTOR) -> Image.Image:
        if scale_factor <= 0:
            raise ValueError(f"scale_factor must be positive, got {scale_factor}")

        mode_key = "balanced" if self.mode == "ultra" else self.mode

        if mode_key in _MODELS:
            try:
                result = self._onnx_upscale(image, mode_key)
                if result is not None:
                    # Always resize to the exact requested scale_factor
                    target = (
                        int(image.width  * scale_factor),
                        int(image.height * scale_factor),
                    )
                    if result.size != target:
                        result = result.resize(target, Image.LANCZOS)
                    return result
            except Exception as exc:
                logger.warning("ONNX upscale failed (%s), falling back: %s", self.mode, exc)

        return self._lanczos_upscale(image, scale_factor)

    # ── ONNX inference ────────────────────────────────────────────────────────

    def _onnx_upscale(self, image: Image.Image, mode_key: str):
        session = self._get_session(mode_key)
        if session is None:
            return None

        img_rgb = image.convert("RGB")
        arr = np.array(img_rgb, dtype=np.float32) / 255.0   # HWC [0,1]
        arr = np.transpose(arr, (2, 0, 1))                   # CHW
        arr = np.expand_dims(arr, 0)                         # NCHW

        input_name = session.get_inputs()[0].name

        try:
            output = session.run(None, {input_name: arr})[0]  # NCHW
        except Exception as exc:
            logger.error("ONNX inference error: %s", exc, exc_info=True)
            return None

        out = np.squeeze(output, 0)                           # CHW
        out = np.transpose(out, (1, 2, 0))                   # HWC
        out = np.clip(out * 255.0, 0, 255).astype(np.uint8)
        return Image.fromarray(out, "RGB")

    def _get_session(self, mode_key: str):
        if mode_key in self._sessions:
            return self._sessions[mode_key]

        try:
            import onnxruntime as ort
        except ImportError:
            logger.warning("onnxruntime not installed.")
            return None

        filename, url, _ = _MODELS[mode_key]
        model_path = self._resolve_model(filename, url)
        if model_path is None:
            return None

        try:
            opts = ort.SessionOptions()
            opts.inter_op_num_threads = 2
            opts.intra_op_num_threads = 4
            opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            session = ort.InferenceSession(
                str(model_path),
                sess_options=opts,
                providers=["CPUExecutionProvider"],
            )
            self._sessions[mode_key] = session
            logger.info("ONNX model loaded: %s", filename)
            return session
        except Exception as exc:
            logger.error("Failed to load ONNX model %s: %s", filename, exc, exc_info=True)
            return None

    def _resolve_model(self, filename: str, url: str):
        models_dir = Path(self.model_manager.root) if self.model_manager else Path("models")
        models_dir.mkdir(exist_ok=True)
        dest = models_dir / filename

        if dest.exists() and dest.stat().st_size > 1_000_000:
            return dest

        logger.info("Downloading model '%s' …", filename)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as f:
                f.write(resp.read())
            if dest.stat().st_size > 1_000_000:
                logger.info("Model downloaded: %s (%.1f MB)", filename, dest.stat().st_size / 1e6)
                return dest
            else:
                logger.error("Downloaded file too small, likely invalid: %s", filename)
                dest.unlink(missing_ok=True)
                return None
        except Exception as exc:
            logger.error("Model download failed for %s: %s", filename, exc)
            if dest.exists():
                dest.unlink(missing_ok=True)
            return None

    # ── Fallback ──────────────────────────────────────────────────────────────

    @staticmethod
    def _lanczos_upscale(image: Image.Image, scale_factor: float) -> Image.Image:
        new_size = (int(image.width * scale_factor), int(image.height * scale_factor))
        logger.debug("Lanczos fallback upscale → %s", new_size)
        return image.resize(new_size, Image.LANCZOS)

    # ── Generic dispatcher ────────────────────────────────────────────────────

    def process(self, image: Image.Image, task: str, **kwargs) -> Image.Image:
        if task == "upscale":
            return self.upscale(image, **kwargs)
        raise NotImplementedError(f"AI task '{task}' not implemented")
