import logging

from PIL import Image, ImageFilter, ImageStat

from utils.constants import BLUR_THUMBNAIL_SIZE, BLUR_RADIUS

logger = logging.getLogger("uic_app")


class SmartBorder:

    @staticmethod
    def build(
        img: Image.Image,
        mode: str,
        width: int,
        height: int,
        color: str,
    ) -> Image.Image:
        """
        Build a background canvas for the given mode.

        Modes:
            blur      — blurred, stretched version of the source image
            dominant  — solid fill using the image's average colour
            normal    — solid fill using the provided hex colour string
        """
        if mode == "blur":
            return SmartBorder._blur_bg(img, width, height)

        if mode == "dominant":
            return SmartBorder._dominant_bg(img, width, height)

        return SmartBorder._solid_bg(width, height, color)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _blur_bg(img: Image.Image, width: int, height: int) -> Image.Image:
        preview = img.copy()
        preview.thumbnail(BLUR_THUMBNAIL_SIZE)
        bg = preview.resize((width, height), Image.LANCZOS)
        return bg.filter(ImageFilter.GaussianBlur(BLUR_RADIUS))

    @staticmethod
    def _dominant_bg(img: Image.Image, width: int, height: int) -> Image.Image:
        # Convert to RGB first to handle RGBA / palette images safely
        rgb = img.convert("RGB")
        stat = ImageStat.Stat(rgb)
        r, g, b = (int(v) for v in stat.mean[:3])
        return Image.new("RGB", (width, height), (r, g, b))

    @staticmethod
    def _solid_bg(width: int, height: int, color: str) -> Image.Image:
        try:
            return Image.new("RGB", (width, height), color)
        except (ValueError, AttributeError):
            logger.warning("Invalid border color '%s', falling back to black.", color)
            return Image.new("RGB", (width, height), "#000000")
