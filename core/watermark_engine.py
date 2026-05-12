"""
WatermarkEngine — adds text or image watermarks to PIL Images.
"""

import logging
import os
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger("uic_app")

# Position map: name → (x_anchor, y_anchor) as fractions of image size
_POSITIONS = {
    "top-left":     (0.02, 0.02),
    "top-right":    (0.98, 0.02),
    "bottom-left":  (0.02, 0.98),
    "bottom-right": (0.98, 0.98),
    "center":       (0.50, 0.50),
}

_ANCHOR_MAP = {
    "top-left":     "lt",
    "top-right":    "rt",
    "bottom-left":  "lb",
    "bottom-right": "rb",
    "center":       "mm",
}


class WatermarkEngine:

    @staticmethod
    def add_text(
        img: Image.Image,
        text: str,
        font_size: int = 36,
        color: str = "#ffffff",
        opacity: int = 128,
        position: str = "bottom-right",
    ) -> Image.Image:
        """
        Add a text watermark to the image.

        Returns a new RGB/RGBA image with the watermark applied.
        """
        if not text.strip():
            return img.copy()

        result = img.convert("RGBA")
        overlay = Image.new("RGBA", result.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Try to load a nice font, fall back to default
        font = WatermarkEngine._load_font(font_size)

        # Parse color + apply opacity
        r, g, b = WatermarkEngine._hex_to_rgb(color)
        fill = (r, g, b, opacity)

        # Calculate position
        fx, fy = _POSITIONS.get(position, (0.98, 0.98))
        x = int(fx * result.width)
        y = int(fy * result.height)
        anchor = _ANCHOR_MAP.get(position, "rb")

        draw.text((x, y), text, font=font, fill=fill, anchor=anchor)

        result = Image.alpha_composite(result, overlay)
        return result.convert("RGB")

    @staticmethod
    def add_logo(
        img: Image.Image,
        logo_path: str,
        opacity: int = 180,
        position: str = "bottom-right",
        scale: float = 0.15,
    ) -> Image.Image:
        """
        Add an image/logo watermark.

        scale: logo size as fraction of the base image width.
        """
        if not logo_path or not os.path.exists(logo_path):
            logger.warning("Watermark logo not found: %s", logo_path)
            return img.copy()

        try:
            logo = Image.open(logo_path).convert("RGBA")
        except Exception as exc:
            logger.error("Cannot open watermark logo: %s", exc)
            return img.copy()

        result = img.convert("RGBA")

        # Scale logo
        target_w = max(1, int(result.width * scale))
        ratio = target_w / logo.width
        target_h = max(1, int(logo.height * ratio))
        logo = logo.resize((target_w, target_h), Image.LANCZOS)

        # Apply opacity
        if opacity < 255:
            r, g, b, a = logo.split()
            a = a.point(lambda v: int(v * opacity / 255))
            logo = Image.merge("RGBA", (r, g, b, a))

        # Calculate paste position
        fx, fy = _POSITIONS.get(position, (0.98, 0.98))
        x = int(fx * result.width  - (fx * logo.width))
        y = int(fy * result.height - (fy * logo.height))
        x = max(0, min(x, result.width  - logo.width))
        y = max(0, min(y, result.height - logo.height))

        result.paste(logo, (x, y), logo)
        return result.convert("RGB")

    # ── Helpers ──────────────────────────────────

    @staticmethod
    def _load_font(size: int) -> ImageFont.FreeTypeFont:
        candidates = [
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    continue
        return ImageFont.load_default()

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple:
        hex_color = hex_color.lstrip("#")
        try:
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except (ValueError, IndexError):
            return (255, 255, 255)
