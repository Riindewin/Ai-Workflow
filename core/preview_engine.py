import logging

from PIL import Image, UnidentifiedImageError

from core.smart_border import SmartBorder
from core.ai_engine import AIEngine
from utils.image_processor import compose_on_background, make_preview
from utils.constants import DEFAULT_SCALE_FACTOR

logger = logging.getLogger("uic_app")


class PreviewEngine:

    def __init__(self, ai_engine: AIEngine = None):
        self.ai_engine = ai_engine or AIEngine()

    def generate(
        self,
        path: str,
        width: int,
        height: int,
        mode: str,
        border_color: str,
        upscale: bool = False,
        ai_mode: str = "low",
    ) -> Image.Image:
        """
        Generate a preview image for the given file.

        If upscale=True the image is upscaled via AIEngine before compositing.
        Returns a thumbnail-sized PIL Image ready for display.
        """
        try:
            # Dosya kapatılmadan önce içerik yüklenir ve kopyalanır
            with Image.open(path) as raw:
                raw.load()
                img = raw.copy()

            if upscale and self.ai_engine:
                self.ai_engine.set_mode(ai_mode)
                img = self.ai_engine.upscale(img, scale_factor=DEFAULT_SCALE_FACTOR)

            bg = SmartBorder.build(img, mode, width, height, border_color)
            composed = compose_on_background(img, bg, width, height)
            return make_preview(composed)

        except UnidentifiedImageError:
            logger.error("PreviewEngine: unsupported image format — %s", path)
            raise
        except OSError as exc:
            logger.error("PreviewEngine: cannot open file %s — %s", path, exc, exc_info=True)
            raise
