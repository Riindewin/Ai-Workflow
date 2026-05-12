import logging
import os
import traceback

from utils.constants import LOG_FOLDER, LOG_FILE


class LoggerService:

    def __init__(self):
        os.makedirs(LOG_FOLDER, exist_ok=True)

        # Use a named logger to avoid conflicts with basicConfig in other modules
        self.logger = logging.getLogger("uic_app")
        self.logger.setLevel(logging.DEBUG)

        if not self.logger.handlers:
            handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

            # Console handler (UTF-8 safe)
            import sys
            console = logging.StreamHandler(sys.stdout)
            console.setLevel(logging.WARNING)
            console.setFormatter(formatter)
            try:
                console.stream.reconfigure(encoding="utf-8")
            except Exception:
                pass
            self.logger.addHandler(console)

    def log(self, text: str) -> None:
        """Log an info-level message."""
        self.logger.info(text)

    def warning(self, text: str) -> None:
        """Log a warning-level message."""
        self.logger.warning(text)

    def error(self, text: str, exc: Exception = None) -> None:
        """
        Log an error message. If an exception is provided,
        the full traceback is written to the log file.
        """
        if exc is not None:
            tb = traceback.format_exc()
            self.logger.error("%s\n%s", text, tb)
        else:
            self.logger.error(text)

    def debug(self, text: str) -> None:
        """Log a debug-level message."""
        self.logger.debug(text)
