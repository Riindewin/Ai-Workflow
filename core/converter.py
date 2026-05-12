import logging
import os

from PIL import Image, UnidentifiedImageError

from core.export_engine import ExportEngine
from core.smart_border import SmartBorder
from utils.image_processor import compose_on_background, fit_image

logger = logging.getLogger("uic_app")


class ImageConverter:

    def __init__(self):
        self.export_engine = ExportEngine()

    def convert(
        self,
        files: list,
        width: int,
        height: int,
        fmt: str,
        quality: int,
        border_mode: str,
        border_color: str,
        output_folder: str,
        metadata_clean: bool = False,
        use_original_size: bool = False,
        progress_callback=None,
        log_callback=None,
    ) -> None:
        """
        Batch-convert a list of image files.

        Each file is resized to fit within (width x height), placed on a
        SmartBorder background, and saved to output_folder.
        """
        total = len(files)
        self.export_engine.ensure_folder(output_folder)

        for index, file in enumerate(files, start=1):
            try:
                self._process_single(
                    file=file,
                    width=width,
                    height=height,
                    fmt=fmt,
                    quality=quality,
                    border_mode=border_mode,
                    border_color=border_color,
                    output_folder=output_folder,
                    metadata_clean=metadata_clean,
                    use_original_size=use_original_size,
                    log_callback=log_callback,
                )

                if progress_callback:
                    progress_callback(index, total)

            except UnidentifiedImageError:
                msg = f"HATA → Desteklenmeyen görsel formatı: {os.path.basename(file)}"
                logger.error(msg)
                if log_callback:
                    log_callback(msg)

            except OSError as exc:
                msg = f"HATA → Dosya okunamadı: {os.path.basename(file)} ({exc})"
                logger.error(msg, exc_info=True)
                if log_callback:
                    log_callback(msg)

            except Exception as exc:  # noqa: BLE001
                msg = f"HATA → {os.path.basename(file)}: {exc}"
                logger.error(msg, exc_info=True)
                if log_callback:
                    log_callback(msg)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_single(
        self,
        file: str,
        width: int,
        height: int,
        fmt: str,
        quality: int,
        border_mode: str,
        border_color: str,
        output_folder: str,
        metadata_clean: bool,
        use_original_size: bool,
        log_callback,
    ) -> None:
        with Image.open(file) as img:
            target_w = img.width  if use_original_size else width
            target_h = img.height if use_original_size else height
            bg = SmartBorder.build(img, border_mode, target_w, target_h, border_color)
            composed = compose_on_background(img, bg, target_w, target_h)

            name = os.path.splitext(os.path.basename(file))[0]
            save_path = os.path.join(output_folder, f"{name}.{fmt}")

            self.export_engine.save_image(composed, save_path, fmt, quality, metadata_clean)

        if log_callback:
            log_callback(f"Kaydedildi → {save_path}")
