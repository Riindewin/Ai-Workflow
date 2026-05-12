import logging
import os

from PIL import Image

logger = logging.getLogger("uic_app")

# Formats that support the quality parameter
_QUALITY_FORMATS = {"JPEG", "WEBP"}

# Formats that do NOT support the exif kwarg for metadata stripping
_NO_EXIF_FORMATS = {"PNG", "BMP", "GIF"}


class ExportEngine:

    @staticmethod
    def ensure_folder(path: str) -> None:
        os.makedirs(path, exist_ok=True)

    def save_image(
        self,
        image: Image.Image,
        path: str,
        fmt: str,
        quality: int,
        metadata_clean: bool,
    ) -> None:
        """
        Save a PIL Image to disk.

        Handles format normalisation (jpg → JPEG), quality for lossy formats,
        and optional EXIF stripping. Raises OSError on write failure.
        """
        folder = os.path.dirname(path)
        if folder:
            self.ensure_folder(folder)

        pil_fmt = self._normalise_format(fmt)

        # PNG / BMP do not accept a quality kwarg
        save_kwargs: dict = {"format": pil_fmt}
        if pil_fmt in _QUALITY_FORMATS:
            save_kwargs["quality"] = quality

        # Strip EXIF only for formats that support the exif kwarg
        if metadata_clean and pil_fmt not in _NO_EXIF_FORMATS:
            save_kwargs["exif"] = b""

        # JPEG requires RGB — convert if necessary
        if pil_fmt == "JPEG" and image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        try:
            image.save(path, **save_kwargs)
            logger.debug("Saved: %s", path)
        except OSError as exc:
            logger.error("Failed to save image to %s: %s", path, exc, exc_info=True)
            raise

    @staticmethod
    def _normalise_format(fmt: str) -> str:
        """Convert user-facing format string to PIL format name."""
        mapping = {"jpg": "JPEG", "jpeg": "JPEG"}
        return mapping.get(fmt.lower(), fmt.upper())
