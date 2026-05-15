"""
ImageEditor — non-destructive image editing operations.

All operations take a PIL Image and return a new PIL Image.
Operations: brightness, contrast, saturation, sharpness, rotate, flip, crop.
"""

import logging
from PIL import Image, ImageEnhance, ImageOps

logger = logging.getLogger("uic_app")


class ImageEditor:

    @staticmethod
    def adjust_brightness(img: Image.Image, factor: float) -> Image.Image:
        """factor: 0.0=black, 1.0=original, 2.0=double brightness"""
        if abs(factor - 1.0) < 0.01:
            return img.copy()
        return ImageEnhance.Brightness(img).enhance(factor)

    @staticmethod
    def adjust_contrast(img: Image.Image, factor: float) -> Image.Image:
        if abs(factor - 1.0) < 0.01:
            return img.copy()
        return ImageEnhance.Contrast(img).enhance(factor)

    @staticmethod
    def adjust_saturation(img: Image.Image, factor: float) -> Image.Image:
        if abs(factor - 1.0) < 0.01:
            return img.copy()
        return ImageEnhance.Color(img).enhance(factor)

    @staticmethod
    def adjust_sharpness(img: Image.Image, factor: float) -> Image.Image:
        if abs(factor - 1.0) < 0.01:
            return img.copy()
        return ImageEnhance.Sharpness(img).enhance(factor)

    @staticmethod
    def apply_all(
        img: Image.Image,
        brightness: float = 1.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        sharpness: float = 1.0,
    ) -> Image.Image:
        """Apply all color corrections in one pass."""
        result = img.copy()
        if abs(brightness - 1.0) > 0.01:
            result = ImageEnhance.Brightness(result).enhance(brightness)
        if abs(contrast - 1.0) > 0.01:
            result = ImageEnhance.Contrast(result).enhance(contrast)
        if abs(saturation - 1.0) > 0.01:
            result = ImageEnhance.Color(result).enhance(saturation)
        if abs(sharpness - 1.0) > 0.01:
            result = ImageEnhance.Sharpness(result).enhance(sharpness)
        return result

    @staticmethod
    def rotate(img: Image.Image, degrees: int, expand: bool = True) -> Image.Image:
        """Rotate image by degrees (90, 180, 270)."""
        return img.rotate(-degrees, expand=expand)

    @staticmethod
    def flip_horizontal(img: Image.Image) -> Image.Image:
        return ImageOps.mirror(img)

    @staticmethod
    def flip_vertical(img: Image.Image) -> Image.Image:
        return ImageOps.flip(img)

    @staticmethod
    def crop(img: Image.Image, rect: tuple) -> Image.Image:
        """
        Crop image using normalized coordinates (0.0-1.0).
        rect: (x1, y1, x2, y2) where all values are 0.0-1.0
        """
        x1, y1, x2, y2 = rect
        w, h = img.width, img.height
        box = (
            int(x1 * w),
            int(y1 * h),
            int(x2 * w),
            int(y2 * h),
        )
        return img.crop(box)

    @staticmethod
    def crop_pixels(img: Image.Image, box: tuple) -> Image.Image:
        """Crop using pixel coordinates (x1, y1, x2, y2)."""
        return img.crop(box)

    @staticmethod
    def apply_grayscale(img: Image.Image) -> Image.Image:
        """Siyah-beyaz filtre."""
        return img.convert("L").convert("RGB")

    @staticmethod
    def apply_sepia(img: Image.Image) -> Image.Image:
        """Sepya filtre."""
        rgb = img.convert("RGB")
        import numpy as np
        arr = np.array(rgb, dtype=np.float32)
        r = arr[:, :, 0] * 0.393 + arr[:, :, 1] * 0.769 + arr[:, :, 2] * 0.189
        g = arr[:, :, 0] * 0.349 + arr[:, :, 1] * 0.686 + arr[:, :, 2] * 0.168
        b = arr[:, :, 0] * 0.272 + arr[:, :, 1] * 0.534 + arr[:, :, 2] * 0.131
        sepia = np.stack([
            np.clip(r, 0, 255),
            np.clip(g, 0, 255),
            np.clip(b, 0, 255),
        ], axis=2).astype(np.uint8)
        return Image.fromarray(sepia, "RGB")

    @staticmethod
    def apply_vivid(img: Image.Image) -> Image.Image:
        """Canlı renkler — doygunluk ×1.4."""
        return ImageEnhance.Color(img.convert("RGB")).enhance(1.4)

    @staticmethod
    def apply_cool(img: Image.Image) -> Image.Image:
        """Soğuk ton — mavi +15, kırmızı -10."""
        rgb = img.convert("RGB")
        import numpy as np
        arr = np.array(rgb, dtype=np.int16)
        arr[:, :, 0] = np.clip(arr[:, :, 0] - 10, 0, 255)
        arr[:, :, 2] = np.clip(arr[:, :, 2] + 15, 0, 255)
        return Image.fromarray(arr.astype(np.uint8), "RGB")

    @staticmethod
    def apply_warm(img: Image.Image) -> Image.Image:
        """Sıcak ton — kırmızı +15, mavi -10."""
        rgb = img.convert("RGB")
        import numpy as np
        arr = np.array(rgb, dtype=np.int16)
        arr[:, :, 0] = np.clip(arr[:, :, 0] + 15, 0, 255)
        arr[:, :, 2] = np.clip(arr[:, :, 2] - 10, 0, 255)
        return Image.fromarray(arr.astype(np.uint8), "RGB")

    @staticmethod
    def apply_vintage(img: Image.Image) -> Image.Image:
        """Vintage — düşük kontrast + hafif sepya."""
        low_contrast = ImageEnhance.Contrast(img.convert("RGB")).enhance(0.85)
        return ImageEditor.apply_sepia(low_contrast)
