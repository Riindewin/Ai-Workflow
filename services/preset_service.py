"""
PresetService — save/load user-defined presets and built-in templates.
"""

import json
import logging
import os

from utils.constants import PRESETS_FILE, PRESET_TEMPLATES

logger = logging.getLogger("uic_app")


class PresetService:

    def __init__(self, path: str = PRESETS_FILE):
        self.path = path
        self._user_presets: dict = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self._user_presets = json.load(f)
            except Exception as exc:
                logger.warning("Could not load presets: %s", exc)
                self._user_presets = {}

    def _save(self) -> None:
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._user_presets, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            logger.error("Could not save presets: %s", exc)

    def all_names(self) -> list[str]:
        """Return all preset names: built-in templates + user presets."""
        return list(PRESET_TEMPLATES.keys()) + list(self._user_presets.keys())

    def get(self, name: str) -> dict | None:
        if name in PRESET_TEMPLATES:
            return dict(PRESET_TEMPLATES[name])
        return dict(self._user_presets.get(name, {})) or None

    def save_user(self, name: str, data: dict) -> None:
        self._user_presets[name] = data
        self._save()

    def delete_user(self, name: str) -> bool:
        if name in self._user_presets:
            del self._user_presets[name]
            self._save()
            return True
        return False

    def list_user(self) -> list[str]:
        """Kullanıcı tanımlı preset isimlerini döndür."""
        return list(self._user_presets.keys())

    def is_builtin(self, name: str) -> bool:
        return name in PRESET_TEMPLATES
