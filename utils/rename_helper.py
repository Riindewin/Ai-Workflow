"""
RenameHelper — apply naming patterns to output file names.

Supported tokens:
  {name}      — original file name without extension
  {date}      — today's date as YYYYMMDD
  {time}      — current time as HHMMSS
  {index}     — 1-based counter (plain)
  {index:03d} — zero-padded counter
  {ext}       — output extension (without dot)
"""

import os
from datetime import datetime


class RenameHelper:

    @staticmethod
    def apply(pattern: str, original_path: str, index: int, ext: str) -> str:
        """
        Apply the naming pattern and return the output filename (with extension).

        Args:
            pattern:       e.g. "{name}_{date}_{index:03d}"
            original_path: source file path
            index:         1-based position in the batch
            ext:           output extension without dot (e.g. "jpg")

        Returns:
            filename with extension, e.g. "photo_20240101_001.jpg"
        """
        name = os.path.splitext(os.path.basename(original_path))[0]
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M%S")

        try:
            result = pattern.format(
                name=name,
                date=date_str,
                time=time_str,
                index=index,
                ext=ext,
            )
        except (KeyError, ValueError):
            # Fallback to safe name if pattern is invalid
            result = f"{name}_{index}"

        # Sanitize: remove characters not safe for filenames
        for ch in r'\/:*?"<>|':
            result = result.replace(ch, "_")

        # Çift uzantı oluşmasını önle
        dot_ext = f".{ext}"
        if result.lower().endswith(dot_ext.lower()):
            return result
        return f"{result}{dot_ext}"

    @staticmethod
    def preview(pattern: str, sample_name: str = "photo", ext: str = "jpg") -> str:
        """Return a preview of what the pattern produces for display in UI."""
        return RenameHelper.apply(pattern, f"{sample_name}.jpg", 1, ext)
