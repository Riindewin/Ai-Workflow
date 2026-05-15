"""
ExifReader — read EXIF/metadata from image files using Pillow.
"""

import logging
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

logger = logging.getLogger("uic_app")

# Human-readable fields to display
DISPLAY_TAGS = [
    "Make", "Model", "DateTime", "DateTimeOriginal",
    "ExposureTime", "FNumber", "ISOSpeedRatings",
    "FocalLength", "Flash", "WhiteBalance",
    "ImageWidth", "ImageLength", "Orientation",
    "Software", "Artist", "Copyright",
    "GPSInfo",
]


class ExifReader:

    @staticmethod
    def read(path: str) -> dict:
        """
        Read EXIF data from an image file.
        Returns a dict of {tag_name: value} for known tags.
        Returns empty dict if no EXIF data found.
        """
        try:
            with Image.open(path) as img:
                # Pillow'un public API'si kullanılır
                exif_data = img.getexif()
                if not exif_data:
                    return {}

                result = {}
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, str(tag_id))
                    if tag == "GPSInfo":
                        result["GPS"] = ExifReader._parse_gps(value)
                    elif tag in DISPLAY_TAGS:
                        result[tag] = ExifReader._format_value(tag, value)

                return result

        except Exception as exc:
            logger.debug("EXIF read failed for %s: %s", path, exc)
            return {}

    @staticmethod
    def get_basic_info(path: str) -> dict:
        """
        Get basic file info (dimensions, format, file size) without EXIF.
        Always succeeds.
        """
        import os
        try:
            with Image.open(path) as img:
                return {
                    "Genişlik": f"{img.width} px",
                    "Yükseklik": f"{img.height} px",
                    "Format": img.format or "?",
                    "Mod": img.mode,
                    "Dosya Boyutu": f"{os.path.getsize(path) / 1024:.1f} KB",
                }
        except Exception:
            return {}

    @staticmethod
    def _format_value(tag: str, value) -> str:
        if tag == "ExposureTime":
            try:
                return f"{float(value):.6f}s".rstrip("0").rstrip(".") + "s"
            except Exception:
                return str(value)
        if tag == "FNumber":
            try:
                return f"f/{float(value):.1f}"
            except Exception:
                return str(value)
        if tag == "FocalLength":
            try:
                return f"{float(value):.0f}mm"
            except Exception:
                return str(value)
        if tag == "ISOSpeedRatings":
            return f"ISO {value}"
        return str(value)

    @staticmethod
    def _parse_gps(gps_info: dict) -> str:
        try:
            # IFDRational dahil tüm GPS değer tiplerini destekler
            def to_deg(val):
                if hasattr(val, "__len__") and len(val) == 3:
                    d, m, s = val
                    return float(d) + float(m) / 60 + float(s) / 3600
                return float(val)

            lat = to_deg(gps_info.get(2, (0, 0, 0)))
            lon = to_deg(gps_info.get(4, (0, 0, 0)))
            lat_ref = gps_info.get(1, "N")
            lon_ref = gps_info.get(3, "E")
            if lat_ref == "S":
                lat = -lat
            if lon_ref == "W":
                lon = -lon
            return f"{lat:.5f}, {lon:.5f}"
        except Exception:
            return "?"
