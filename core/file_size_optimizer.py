"""
FileSizeOptimizer — binary search for the quality value that hits a target file size.
"""

import io
import logging

from PIL import Image

logger = logging.getLogger("uic_app")


class FileSizeOptimizer:

    @staticmethod
    def find_quality(
        img: Image.Image,
        target_kb: int,
        fmt: str = "jpg",
        tolerance_kb: int = 10,
        max_iterations: int = 12,
    ) -> int:
        """
        Binary search for the JPEG/WebP quality that produces a file
        closest to target_kb without exceeding it.

        Returns the optimal quality value (1-95).
        """
        pil_fmt = "JPEG" if fmt.lower() in ("jpg", "jpeg") else fmt.upper()

        if pil_fmt not in ("JPEG", "WEBP"):
            logger.info("FileSizeOptimizer: format %s doesn't support quality, returning 95", fmt)
            return 95

        rgb = img.convert("RGB")
        target_bytes = target_kb * 1024

        lo, hi = 1, 95
        best_quality = lo  # Geçerli bir başlangıç değeri

        for _ in range(max_iterations):
            mid = (lo + hi) // 2
            buf = io.BytesIO()
            rgb.save(buf, format=pil_fmt, quality=mid)
            size = buf.tell()

            if size <= target_bytes:
                best_quality = mid
                lo = mid + 1
            else:
                hi = mid - 1

            if hi - lo <= 1:
                break

        logger.debug(
            "FileSizeOptimizer: target=%dKB, quality=%d, achieved=%.1fKB",
            target_kb, best_quality,
            FileSizeOptimizer._measure_kb(rgb, pil_fmt, best_quality),
        )
        return best_quality

    @staticmethod
    def _measure_kb(img: Image.Image, pil_fmt: str, quality: int) -> float:
        buf = io.BytesIO()
        img.save(buf, format=pil_fmt, quality=quality)
        return buf.tell() / 1024
