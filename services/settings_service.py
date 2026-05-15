import json
import logging
import os

from utils.constants import (
    SETTINGS_FILE,
    DEFAULT_OUTPUT_FOLDER,
    DEFAULT_BORDER_COLOR,
    DEFAULT_OUTPUT_WIDTH,
    DEFAULT_OUTPUT_HEIGHT,
    DEFAULT_QUALITY,
    DEFAULT_FORMAT,
    DEFAULT_BORDER_MODE,
    DEFAULT_AI_MODE,
)

logger = logging.getLogger("uic_app")

# Uygulama genelinde kullanılan varsayılan ayarlar
DEFAULTS: dict = {
    "output_folder":   DEFAULT_OUTPUT_FOLDER,
    "border_color":    DEFAULT_BORDER_COLOR,
    "dark_mode":       True,
    "width":           DEFAULT_OUTPUT_WIDTH,
    "height":          DEFAULT_OUTPUT_HEIGHT,
    "quality":         DEFAULT_QUALITY,
    "format":          DEFAULT_FORMAT,
    "border_mode":     DEFAULT_BORDER_MODE,
    "metadata_clean":  False,
    "ai_mode":         DEFAULT_AI_MODE,
    "use_original_size": False,
    "rename_pattern":  "{name}",
    "target_size_kb":  0,
    "theme":           "dark",
    "watch_folder":    "",
    "auto_remove_processed": False,
    "auto_save":             False,
}


class SettingsService:

    def __init__(self, path: str = SETTINGS_FILE):
        self.path = path

    def load(self) -> dict:
        """
        Load settings from disk. Falls back to DEFAULTS for any missing or
        invalid key so the application never crashes on a corrupt settings file.
        """
        data: dict = {}

        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    logger.warning(
                        "settings.json did not contain a JSON object — using defaults."
                    )
                    data = {}
            except json.JSONDecodeError as exc:
                logger.error(
                    "settings.json is malformed (%s) — using defaults.", exc
                )
                data = {}
            except OSError as exc:
                logger.error(
                    "Could not read settings.json (%s) — using defaults.", exc
                )
                data = {}

        # Merge with defaults so every key is always present
        merged = {**DEFAULTS, **data}
        return merged

    def save(self, data: dict) -> bool:
        """
        Persist settings to disk. Returns True on success, False on failure.
        """
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except OSError as exc:
            logger.error("Could not save settings.json: %s", exc)
            return False
