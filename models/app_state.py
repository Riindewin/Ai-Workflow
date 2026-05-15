from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AppState:
    # ── Files ─────────────────────────────────
    files: list = field(default_factory=list)

    # ── Output ────────────────────────────────
    output_folder: str = "outputs"
    fmt: str = "jpg"
    quality: int = 95
    metadata_clean: bool = False
    use_original_size: bool = False

    # ── Dimensions ────────────────────────────
    width: int = 1500
    height: int = 1500

    # ── Border ────────────────────────────────
    border_color: str = "#000000"
    border_mode: str = "normal"

    # ── AI ────────────────────────────────────
    ai_mode: str = "low"

    # ── Rename pattern ────────────────────────
    rename_pattern: str = "{name}"

    # ── Target file size (KB, 0 = disabled) ───
    target_size_kb: int = 0

    # ── Watermark ─────────────────────────────
    watermark_text: str = ""
    watermark_font_size: int = 36
    watermark_color: str = "#ffffff"
    watermark_opacity: int = 128   # 0-255
    watermark_position: str = "bottom-right"
    watermark_logo_path: str = ""

    # ── Color correction ──────────────────────
    brightness: float = 1.0   # 0.0 - 2.0
    contrast: float = 1.0
    saturation: float = 1.0
    sharpness: float = 1.0

    # ── Crop ──────────────────────────────────
    crop_rect: Optional[tuple] = None   # (x1, y1, x2, y2) normalized 0-1

    # ── Watch mode ────────────────────────────
    watch_folder: str = ""
    watch_active: bool = False

    # ── UI preferences ────────────────────────
    # UI preferences
    auto_remove_processed: bool = False

    # ── Auto-save ─────────────────────────────
    auto_save: bool = False

    # ── Batch ─────────────────────────────────
    batch_cancel: bool = False
