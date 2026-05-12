"""
Shared image processing utilities.
Eliminates code duplication between converter.py and preview_engine.py.
"""

from PIL import Image

from utils.constants import PREVIEW_THUMBNAIL_SIZE


def fit_image(img: Image.Image, width: int, height: int) -> tuple[Image.Image, int, int, int, int]:
    """
    Resize image to fit within (width x height) while preserving aspect ratio.

    Returns:
        (resized_image, new_w, new_h, paste_x, paste_y)
    """
    ratio = min(width / img.width, height / img.height)
    new_w = int(img.width * ratio)
    new_h = int(img.height * ratio)

    resized = img.resize((new_w, new_h), Image.LANCZOS)

    x = (width - new_w) // 2
    y = (height - new_h) // 2

    return resized, new_w, new_h, x, y


def compose_on_background(img: Image.Image, bg: Image.Image, width: int, height: int) -> Image.Image:
    """
    Fit img onto bg canvas centered. Returns the composed image.
    bg is copied before pasting to avoid mutating the original background.
    """
    resized, _, _, x, y = fit_image(img, width, height)
    canvas = bg.copy()  # Fix #7: don't mutate the original bg in-place
    canvas.paste(resized, (x, y))
    return canvas


def make_preview(composed: Image.Image, max_size: tuple[int, int] = PREVIEW_THUMBNAIL_SIZE) -> Image.Image:
    """
    Create a preview-sized copy of the composed image.
    """
    preview = composed.copy()
    preview.thumbnail(max_size)
    return preview
