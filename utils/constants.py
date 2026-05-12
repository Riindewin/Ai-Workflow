# ─────────────────────────────────────────────
#  Application-wide constants
# ─────────────────────────────────────────────

APP_NAME    = "Ultimate Image Converter AI"
APP_VERSION = "3.1.0"

# ── Window ────────────────────────────────────
DEFAULT_WINDOW_WIDTH  = 1500
DEFAULT_WINDOW_HEIGHT = 900
DEFAULT_WINDOW_MIN_W  = 1100
DEFAULT_WINDOW_MIN_H  = 700

# ── Image defaults ────────────────────────────
DEFAULT_OUTPUT_WIDTH  = 1500
DEFAULT_OUTPUT_HEIGHT = 1500
DEFAULT_QUALITY       = 95
DEFAULT_FORMAT        = "jpg"
DEFAULT_BORDER_MODE   = "normal"
DEFAULT_BORDER_COLOR  = "#000000"
DEFAULT_AI_MODE       = "low"
DEFAULT_OUTPUT_FOLDER = "outputs"

# ── Supported values ──────────────────────────
SUPPORTED_FORMATS      = ["jpg", "png", "webp", "bmp"]
SUPPORTED_BORDER_MODES = ["normal", "blur", "dominant"]
SUPPORTED_AI_MODES     = ["low", "balanced", "ultra"]
SUPPORTED_IMAGE_EXTS   = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff", ".tif"}

# ── Preview ───────────────────────────────────
PREVIEW_MAX_WIDTH      = 800
PREVIEW_MAX_HEIGHT     = 650
PREVIEW_THUMBNAIL_SIZE = (PREVIEW_MAX_WIDTH, PREVIEW_MAX_HEIGHT)

# ── Smart border ──────────────────────────────
BLUR_THUMBNAIL_SIZE = (1200, 1200)
BLUR_RADIUS         = 12

# ── AI ────────────────────────────────────────
DEFAULT_SCALE_FACTOR = 2.0

# ── Layout ────────────────────────────────────
SIDEBAR_WIDTH  = 280
RIGHT_PANEL_W  = 320
TOPBAR_H       = 52
TAB_BAR_H      = 44
ACTION_BAR_H   = 64
STATUSBAR_H    = 28

# ── Tab names ─────────────────────────────────
TAB_CONVERTER  = "🖼  Dönüştürücü"
TAB_AI         = "🤖  AI Araçları"
TAB_EDITOR     = "✂  Düzenleyici"
TAB_BATCH      = "📦  Batch & Export"
TAB_SETTINGS   = "⚙  Ayarlar"
TAB_INFO       = "ℹ  Bilgi"

TABS = [TAB_CONVERTER, TAB_AI, TAB_EDITOR, TAB_BATCH, TAB_SETTINGS, TAB_INFO]

# ── Preset templates ──────────────────────────
PRESET_TEMPLATES = {
    "Instagram Kare":    {"width": 1080, "height": 1080, "format": "jpg", "quality": 90},
    "Instagram Story":   {"width": 1080, "height": 1920, "format": "jpg", "quality": 90},
    "Twitter Banner":    {"width": 1500, "height": 500,  "format": "jpg", "quality": 85},
    "Twitter Post":      {"width": 1200, "height": 675,  "format": "jpg", "quality": 85},
    "Facebook Cover":    {"width": 820,  "height": 312,  "format": "jpg", "quality": 85},
    "YouTube Thumbnail": {"width": 1280, "height": 720,  "format": "jpg", "quality": 90},
    "Print A4":          {"width": 2480, "height": 3508, "format": "png", "quality": 100},
    "Print A5":          {"width": 1748, "height": 2480, "format": "png", "quality": 100},
    "Wallpaper FHD":     {"width": 1920, "height": 1080, "format": "jpg", "quality": 95},
    "Wallpaper 4K":      {"width": 3840, "height": 2160, "format": "jpg", "quality": 95},
}

# ── Rename patterns ───────────────────────────
RENAME_PATTERNS = [
    "{name}",
    "{name}_{date}",
    "{name}_{index}",
    "{name}_{date}_{index}",
    "{index}_{name}",
    "processed_{name}",
    "output_{index:03d}",
]

# ── Dark theme palette ────────────────────────
C_BG_BASE    = "#0f0f0f"
C_BG_SURFACE = "#161616"
C_BG_RAISED  = "#1e1e1e"
C_BG_INPUT   = "#252525"
C_BG_HOVER   = "#2a2a2a"

C_BORDER     = "#2d2d2d"
C_BORDER_LT  = "#3a3a3a"

C_TEXT       = "#e8e8e8"
C_TEXT_MUTED = "#888888"
C_TEXT_DIM   = "#555555"

C_ACCENT     = "#00c896"
C_ACCENT_DIM = "#009e78"
C_ACCENT_ALT = "#00a8ff"
C_ACCENT_RED = "#e05555"
C_ACCENT_PUR = "#9b59b6"
C_ACCENT_ORG = "#f0a500"

C_SUCCESS = "#00c896"
C_WARNING = "#f0a500"
C_ERROR   = "#e05555"
C_LOG_FG  = "#39d98a"

# ── Light theme palette ───────────────────────
L_BG_BASE    = "#f0f0f0"
L_BG_SURFACE = "#e8e8e8"
L_BG_RAISED  = "#ffffff"
L_BG_INPUT   = "#ffffff"
L_BG_HOVER   = "#d8d8d8"
L_BORDER     = "#cccccc"
L_BORDER_LT  = "#bbbbbb"
L_TEXT       = "#1a1a1a"
L_TEXT_MUTED = "#666666"
L_LOG_FG     = "#007a50"

# ── Files ─────────────────────────────────────
SETTINGS_FILE  = "settings.json"
PRESETS_FILE   = "presets.json"
LOG_FOLDER     = "logs"
LOG_FILE       = "logs/app.log"
MODELS_FOLDER  = "models"
CACHE_FOLDER   = "cache"
