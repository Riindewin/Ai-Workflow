"""
WatchService — monitors a folder for new image files and triggers a callback.
Uses polling (no external dependency) for maximum compatibility.
"""

import logging
import os
import threading
import time

from utils.constants import SUPPORTED_IMAGE_EXTS

logger = logging.getLogger("uic_app")

POLL_INTERVAL = 2.0  # seconds


class WatchService:

    def __init__(self, callback):
        """
        callback(path: str) — called for each new image file detected.
        """
        self._callback = callback
        self._folder: str = ""
        self._seen: set = set()
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self, folder: str) -> None:
        if self._running:
            self.stop()

        if not os.path.isdir(folder):
            logger.warning("WatchService: folder does not exist: %s", folder)
            return

        self._folder = folder
        self._seen = set(self._scan())
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("WatchService started: %s", folder)

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
            self._thread = None
        logger.info("WatchService stopped")

    def is_running(self) -> bool:
        return self._running

    # ── Internal ─────────────────────────────────

    def _loop(self) -> None:
        while self._running:
            time.sleep(POLL_INTERVAL)
            try:
                current = set(self._scan())
                new_files = current - self._seen
                self._seen = current
                for path in sorted(new_files):
                    logger.info("WatchService: new file detected: %s", path)
                    try:
                        self._callback(path)
                    except Exception as exc:
                        logger.error("WatchService callback error: %s", exc)
            except Exception as exc:
                logger.error("WatchService poll error: %s", exc)

    def _scan(self) -> list[str]:
        try:
            return [
                os.path.join(self._folder, f)
                for f in os.listdir(self._folder)
                if os.path.splitext(f)[1].lower() in SUPPORTED_IMAGE_EXTS
            ]
        except Exception:
            return []
