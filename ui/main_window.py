"""
MainWindow — ana pencere ve controller.

Layout:
  TOPBAR (52px) | FILE PANEL (280px) | ZOOM/PAN CANVAS | RIGHT PANEL (320px)
  ACTION BAR (64px)
"""

from __future__ import annotations

import logging
import os
import threading
import zipfile
from typing import Optional

from PIL import Image

import tkinter as tk
from tkinter import Frame, Label, Button, X, Y, LEFT, RIGHT, BOTH, TOP, BOTTOM

try:
    from tkinterdnd2 import DND_FILES
    _DND_AVAILABLE = True
except ImportError:
    _DND_AVAILABLE = False

from core.ai_engine import AIEngine
from core.converter import ImageConverter
from core.export_engine import ExportEngine
from core.image_editor import ImageEditor
from core.watermark_engine import WatermarkEngine
from core.preview_engine import PreviewEngine
from core.file_size_optimizer import FileSizeOptimizer
from core.theme_engine import ThemeEngine

from services.settings_service import SettingsService
from services.preset_service import PresetService
from services.rembg_service import RemBGService
from services.watch_service import WatchService
from services.logger_service import LoggerService
from services.model_manager import ModelManager

from models.app_state import AppState

from ui.panels.file_panel import FilePanel
from ui.panels.zoom_pan_canvas import ZoomPanCanvas
from ui.panels.button_panel import ButtonPanel

from ui.tabs.converter_tab import ConverterTab
from ui.tabs.ai_tab import AITab
from ui.tabs.editor_tab import EditorTab
from ui.tabs.batch_tab import BatchTab
from ui.tabs.settings_tab import SettingsTab
from ui.tabs.info_tab import InfoTab

from ui.dialogs.picker_dialogs import ask_open_files, ask_directory
from ui.dialogs.keyboard_shortcuts import KeyboardShortcutsWindow
from ui.widgets.split_button import SplitButton

from utils.constants import (
    APP_NAME, APP_VERSION,
    DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_MIN_W, DEFAULT_WINDOW_MIN_H,
    TOPBAR_H, ACTION_BAR_H, RIGHT_PANEL_W,
    TABS, TAB_CONVERTER, TAB_AI, TAB_EDITOR, TAB_BATCH, TAB_SETTINGS, TAB_INFO,
    C_BG_BASE, C_BG_SURFACE, C_BG_RAISED, C_BG_INPUT,
    C_BORDER, C_TEXT, C_TEXT_MUTED, C_ACCENT,
    SUPPORTED_IMAGE_EXTS,
)
from utils.themes import ALL_THEMES, DEFAULT_THEME, ThemePalette
from utils.rename_helper import RenameHelper

logger = logging.getLogger("uic_app")


class MainWindow:
    """Ana pencere ve controller."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self._theme_name: str = DEFAULT_THEME

        # ── Services ─────────────────────────────
        self.settings_svc = SettingsService()
        self.preset_svc = PresetService()
        self.watch_svc = WatchService(callback=self._on_watch_file)
        self.logger_svc = LoggerService()

        # ── Core engines ─────────────────────────
        self.model_manager = ModelManager()
        self.ai_engine = AIEngine(model_manager=self.model_manager)
        self.converter = ImageConverter()
        self.export_engine = ExportEngine()
        self.image_editor = ImageEditor()
        self.watermark_engine = WatermarkEngine()
        self.preview_engine = PreviewEngine(self.ai_engine)
        self.optimizer = FileSizeOptimizer()

        # ── State ────────────────────────────────
        self.state = AppState()
        self._load_settings()

        # ── Buffer & undo ────────────────────────
        self._buffer: dict[str, Image.Image] = {}
        self._undo_stack: list[tuple[str, Image.Image]] = []
        self._redo_stack: list[tuple[str, Image.Image]] = []
        self._MAX_UNDO = 20  # Fix #9: cap undo stack to avoid unbounded memory growth
        self._current_path: str = ""       # şu an görüntülenen dosya yolu
        self._current_image: Image.Image | None = None  # şu an görüntülenen PIL image
        self._preview_debounce_id = None   # Fix #11: debounce preview updates

        # ── Window setup ─────────────────────────
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry(f"{DEFAULT_WINDOW_WIDTH}x{DEFAULT_WINDOW_HEIGHT}")
        self.root.minsize(DEFAULT_WINDOW_MIN_W, DEFAULT_WINDOW_MIN_H)
        self.root.configure(bg=C_BG_BASE)

        # ── Build UI ─────────────────────────────
        self._build_topbar()
        self._build_main_area()
        self._build_action_bar()

        # ── Theme engine ─────────────────────────
        self.theme_engine = ThemeEngine(self.root)
        self._register_theme_components()
        self.theme_engine.apply(self._theme_name, animated=False)

        # ── Keyboard shortcuts ───────────────────
        self._bind_shortcuts()

        # ── Drag & drop ──────────────────────────
        self._setup_dnd()

        # ── Widget'ları settings'den başlat (Req 9.5, Task 9.7) ──
        self._init_widgets_from_settings()

        # ── Window close ─────────────────────────
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.log(f"✅ {APP_NAME} v{APP_VERSION} başlatıldı")

    # ══════════════════════════════════════════════════════════════════════════
    #  UI BUILDING
    # ══════════════════════════════════════════════════════════════════════════

    def _build_topbar(self) -> None:
        """52px üst bar: uygulama adı | dönüştür split button | status."""
        self._topbar = Frame(self.root, bg=C_BG_SURFACE, height=TOPBAR_H)
        self._topbar.pack(fill=X, side=TOP)
        self._topbar.pack_propagate(False)

        # Separator bottom
        Frame(self._topbar, bg=C_BORDER, height=1).pack(side=BOTTOM, fill=X)

        inner = Frame(self._topbar, bg=C_BG_SURFACE)
        inner.pack(fill=BOTH, expand=True, padx=14)

        # App name
        Label(
            inner, text=f"✨ {APP_NAME}",
            bg=C_BG_SURFACE, fg=C_TEXT,
            font=("Segoe UI", 11, "bold"), anchor="w",
        ).pack(side=LEFT, pady=10)

        # Status label (right side)
        self._topbar_status = Label(
            inner, text="Hazır",
            bg=C_BG_SURFACE, fg=C_TEXT_MUTED,
            font=("Segoe UI", 9), anchor="e",
        )
        self._topbar_status.pack(side=RIGHT, padx=(8, 0))

        # Convert split button (center-right)
        self._convert_btn = SplitButton(
            inner,
            main_text="✨ Dönüştür",
            main_command=self.start_convert,
            menu_items=[
                ("🚀  AI Upscale", self.upscale_selected),
                ("🪄  Arka Plan Kaldır", self.remove_background_selected),
            ],
            bg=C_ACCENT,
            hover="#009e78",
        )
        self._convert_btn.pack(side=RIGHT, padx=(0, 12), pady=8)

    def _build_main_area(self) -> None:
        """Orta alan: FilePanel | ZoomPanCanvas | Right Sidebar."""
        self._main_frame = Frame(self.root, bg=C_BG_BASE)
        self._main_frame.pack(fill=BOTH, expand=True)

        # ── Left: FilePanel ──────────────────────
        self.file_panel = FilePanel(self._main_frame, controller=self)

        # ── Right: Tab sidebar ───────────────────
        self._right_panel = Frame(self._main_frame, bg=C_BG_SURFACE, width=RIGHT_PANEL_W)
        self._right_panel.pack(side=RIGHT, fill=Y)
        self._right_panel.pack_propagate(False)

        self._build_tab_bar()

        # ── Center: ZoomPanCanvas ────────────────
        self.zoom_canvas = ZoomPanCanvas(self._main_frame, controller=self)
        self.zoom_canvas.pack(side=LEFT, fill=BOTH, expand=True)

    def _build_tab_bar(self) -> None:
        """Sağ panelde custom tab bar + tab içerikleri."""
        # Tab bar (44px)
        tab_bar = Frame(self._right_panel, bg=C_BG_SURFACE, height=44)
        tab_bar.pack(fill=X, side=TOP)
        tab_bar.pack_propagate(False)
        Frame(self._right_panel, bg=C_BORDER, height=1).pack(fill=X)

        # Tab content area
        self._tab_content = Frame(self._right_panel, bg=C_BG_SURFACE)
        self._tab_content.pack(fill=BOTH, expand=True)

        # Build tabs
        self.converter_tab = ConverterTab(self._tab_content, controller=self, state=self.state)
        self.ai_tab = AITab(self._tab_content, controller=self, state=self.state)
        self.editor_tab = EditorTab(self._tab_content, controller=self, state=self.state)
        self.batch_tab = BatchTab(self._tab_content, controller=self, state=self.state)
        self.settings_tab = SettingsTab(self._tab_content, controller=self, state=self.state)
        self.info_tab = InfoTab(self._tab_content, controller=self, state=self.state)

        self._tabs: dict[str, Frame] = {
            TAB_CONVERTER: self.converter_tab,
            TAB_AI:        self.ai_tab,
            TAB_EDITOR:    self.editor_tab,
            TAB_BATCH:     self.batch_tab,
            TAB_SETTINGS:  self.settings_tab,
            TAB_INFO:      self.info_tab,
        }

        # Tab buttons
        self._tab_btns: dict[str, Button] = {}
        short_labels = {
            TAB_CONVERTER: "🖼 Dönüştür",
            TAB_AI:        "🤖 AI",
            TAB_EDITOR:    "✂ Düzenle",
            TAB_BATCH:     "📦 Batch",
            TAB_SETTINGS:  "⚙ Ayarlar",
            TAB_INFO:      "ℹ Bilgi",
        }
        for tab_name in TABS:
            btn = Button(
                tab_bar,
                text=short_labels.get(tab_name, tab_name),
                bg=C_BG_SURFACE, fg=C_TEXT_MUTED,
                relief="flat", bd=0, cursor="hand2",
                font=("Segoe UI", 8),
                command=lambda n=tab_name: self._switch_tab(n),
                padx=6,
            )
            btn.pack(side=LEFT, fill=Y)
            self._tab_btns[tab_name] = btn

        self._active_tab: str = TAB_CONVERTER
        self._switch_tab(TAB_CONVERTER)

    def _switch_tab(self, tab_name: str) -> None:
        """Aktif tab'ı değiştir."""
        for name, frame in self._tabs.items():
            frame.pack_forget()
        self._tabs[tab_name].pack(fill=BOTH, expand=True)
        self._active_tab = tab_name

        palette = ALL_THEMES.get(self._theme_name, ALL_THEMES[DEFAULT_THEME])
        for name, btn in self._tab_btns.items():
            if name == tab_name:
                btn.configure(bg=palette.bg_raised, fg=palette.accent)
            else:
                btn.configure(bg=palette.bg_surface, fg=palette.text_muted)

    def _build_action_bar(self) -> None:
        """64px alt action bar."""
        self.button_panel = ButtonPanel(self.root, controller=self)
        self.button_panel.frame.pack(fill=X, side=BOTTOM)

    # ══════════════════════════════════════════════════════════════════════════
    #  THEME & SETTINGS
    # ══════════════════════════════════════════════════════════════════════════

    def _register_theme_components(self) -> None:
        """Tüm panelleri ThemeEngine'e kaydet."""
        self.theme_engine.register(self)
        self.theme_engine.register(self.file_panel)
        self.theme_engine.register(self.zoom_canvas)
        self.theme_engine.register(self.button_panel)
        self.theme_engine.register(self.settings_tab)
        self.theme_engine.register(self.info_tab)

    def apply_theme(self, palette: ThemePalette) -> None:
        """ThemeEngine tarafından çağrılır."""
        # Root & main frames
        self.root.configure(bg=palette.bg_base)
        self._topbar.configure(bg=palette.bg_surface)
        self._main_frame.configure(bg=palette.bg_base)
        self._right_panel.configure(bg=palette.bg_surface)
        self._tab_content.configure(bg=palette.bg_surface)

        # Topbar widgets
        for child in self._topbar.winfo_children():
            try:
                child.configure(bg=palette.bg_surface)
            except Exception:
                pass
        try:
            self._topbar_status.configure(bg=palette.bg_surface, fg=palette.text_muted)
        except Exception:
            pass

        # Tab bar buttons
        for name, btn in self._tab_btns.items():
            if name == self._active_tab:
                btn.configure(bg=palette.bg_raised, fg=palette.accent,
                              activebackground=palette.bg_hover)
            else:
                btn.configure(bg=palette.bg_surface, fg=palette.text_muted,
                              activebackground=palette.bg_hover)

        # Tabs that support apply_theme(palette)
        for tab in (self.converter_tab, self.ai_tab, self.editor_tab,
                    self.batch_tab, self.settings_tab, self.info_tab):
            try:
                tab.apply_theme(palette.bg_surface, palette.bg_input,
                                palette.border, palette.text)
            except Exception:
                pass

        # ButtonPanel tema güncellemesi (Req 5.4, Task 9.6)
        try:
            self.button_panel.apply_theme(palette)
        except Exception:
            pass
        # SplitButton tema güncellemesi
        try:
            self._convert_btn.apply_theme(palette.accent, palette.accent_dim, palette.btn_fg)
        except Exception:
            pass

    def apply_theme_by_name(self, name: str) -> None:
        self._theme_name = name
        self.theme_engine.apply(name, animated=True)
        # Refresh active tab highlight
        self._switch_tab(self._active_tab)

    def _load_settings(self) -> None:
        """settings.json'dan ayarları yükle ve AppState'e uygula."""
        try:
            data = self.settings_svc.load()
            # Output folder: erişilebilir değilse varsayılana dön
            saved_folder = data.get("output_folder", self.state.output_folder)
            try:
                os.makedirs(saved_folder, exist_ok=True)
                self.state.output_folder = saved_folder
            except (PermissionError, OSError):
                self.state.output_folder = os.path.abspath("outputs")
                os.makedirs(self.state.output_folder, exist_ok=True)
            self.state.fmt = data.get("format", self.state.fmt)
            self.state.quality = data.get("quality", self.state.quality)
            self.state.width = data.get("width", self.state.width)
            self.state.height = data.get("height", self.state.height)
            self.state.border_color = data.get("border_color", self.state.border_color)
            self.state.border_mode = data.get("border_mode", self.state.border_mode)
            self.state.metadata_clean = data.get("metadata_clean", self.state.metadata_clean)
            self.state.ai_mode = data.get("ai_mode", self.state.ai_mode)
            self.state.use_original_size = data.get("use_original_size", self.state.use_original_size)
            self.state.auto_remove_processed = data.get("auto_remove_processed", self.state.auto_remove_processed)
            self.state.auto_save = data.get("auto_save", self.state.auto_save)
            self._theme_name = data.get("theme", DEFAULT_THEME)
        except Exception as exc:
            logger.error("Settings yüklenemedi: %s", exc)
            self.state.output_folder = os.path.abspath("outputs")
            os.makedirs(self.state.output_folder, exist_ok=True)

    def _init_widgets_from_settings(self) -> None:
        """AppState değerlerini tüm tab widget'larına uygula. (Req 9.5, Task 9.7)"""
        try:
            self.converter_tab.format_var.set(self.state.fmt)
            self.converter_tab.quality_var.set(self.state.quality)
            self.converter_tab.width_var.set(str(self.state.width))
            self.converter_tab.height_var.set(str(self.state.height))
            self.converter_tab.border_mode_var.set(self.state.border_mode)
            self.converter_tab.original_size_var.set(self.state.use_original_size)
            self.converter_tab.metadata_var.set(self.state.metadata_clean)
            self.converter_tab.folder_var.set(self.state.output_folder)
            self.converter_tab._on_original_toggle()
        except Exception as exc:
            logger.warning("ConverterTab widget init hatası: %s", exc)
        try:
            self.ai_tab.sync_ai_mode(self.state.ai_mode)
        except Exception as exc:
            logger.warning("AITab widget init hatası: %s", exc)

    def _save_settings(self) -> None:
        """Uygulama kapanırken ayarları kaydet."""
        try:
            data = {
                "version":              APP_VERSION,
                "output_folder":        self.state.output_folder,
                "format":               self.state.fmt,
                "quality":              self.state.quality,
                "width":                self.state.width,
                "height":               self.state.height,
                "border_color":         self.state.border_color,
                "border_mode":          self.state.border_mode,
                "metadata_clean":       self.state.metadata_clean,
                "ai_mode":              self.state.ai_mode,
                "use_original_size":    self.state.use_original_size,
                "rename_pattern":       self.state.rename_pattern,
                "target_size_kb":       self.state.target_size_kb,
                "theme":                self._theme_name,
                "watch_folder":         self.state.watch_folder,
                "auto_remove_processed": self.state.auto_remove_processed,
                "auto_save":            self.state.auto_save,
                "batch_cancel":         False,
            }
            self.settings_svc.save(data)
        except Exception as exc:
            logger.error("Settings kaydedilemedi: %s", exc)

    # ══════════════════════════════════════════════════════════════════════════
    #  KEYBOARD SHORTCUTS & DND
    # ══════════════════════════════════════════════════════════════════════════

    def _bind_shortcuts(self) -> None:
        self.root.bind("<Control-o>", lambda _: self.select_files())
        self.root.bind("<Control-O>", lambda _: self.select_files())
        self.root.bind("<Control-s>", lambda _: self.save_buffer())
        self.root.bind("<Control-S>", lambda _: self.save_buffer())
        self.root.bind("<Control-z>", lambda _: self.undo())
        self.root.bind("<Control-Z>", lambda _: self.undo())
        self.root.bind("<Control-y>", lambda _: self.redo())
        self.root.bind("<Control-Y>", lambda _: self.redo())
        self.root.bind("<Delete>",    lambda _: self.remove_selected())
        self.root.bind("<Control-a>", lambda _: self.select_all_files())
        self.root.bind("<Control-A>", lambda _: self.select_all_files())
        self.root.bind("<Escape>",    lambda _: self.cancel_crop())
        self.root.bind("?",           lambda _: KeyboardShortcutsWindow(self.root))
        self.root.bind("<space>",     lambda e: self.start_convert() if e.widget == self.root else None)
        self.root.bind("u",           lambda _: self.upscale_selected())
        self.root.bind("U",           lambda _: self.upscale_selected())
        self.root.bind("r",           lambda _: self.rotate_image(90))
        self.root.bind("R",           lambda _: self.rotate_image(90))
        self.root.bind("f",           lambda _: self.flip_image("h"))
        self.root.bind("F",           lambda _: self.flip_image("h"))
        self.root.bind("c",           lambda _: self.start_crop_mode())
        self.root.bind("C",           lambda _: self.start_crop_mode())
        self.root.bind("b",           lambda _: self.remove_background_selected())
        self.root.bind("B",           lambda _: self.remove_background_selected())

    def _setup_dnd(self) -> None:
        """Drag & drop desteği — canvas ve file_panel üzerine."""
        if not _DND_AVAILABLE:
            return
        # ZoomPanCanvas üzerine DnD
        try:
            self.zoom_canvas.canvas.drop_target_register(DND_FILES)
            self.zoom_canvas.canvas.dnd_bind("<<Drop>>", self._on_dnd_drop)
        except Exception as exc:
            logger.warning("Canvas DnD kurulumu başarısız: %s", exc)
        # FilePanel üzerine DnD (varsa)
        if hasattr(self, "file_panel"):
            try:
                self.file_panel.listbox.drop_target_register(DND_FILES)
                self.file_panel.listbox.dnd_bind("<<Drop>>", self._on_dnd_drop)
            except Exception as exc:
                logger.warning("FilePanel DnD kurulumu başarısız: %s", exc)

    def _on_dnd_drop(self, event) -> None:
        """Sürükle-bırak ile dosya ekleme."""
        try:
            raw = event.data
            # tkinterdnd2 paths may be wrapped in braces for paths with spaces
            paths = self.root.tk.splitlist(raw)
            added = []
            for p in paths:
                p = p.strip()
                if os.path.isfile(p):
                    ext = os.path.splitext(p)[1].lower()
                    if ext in SUPPORTED_IMAGE_EXTS and p not in self.state.files:
                        self.state.files.append(p)
                        added.append(p)
                elif os.path.isdir(p):
                    for fname in os.listdir(p):
                        fp = os.path.join(p, fname)
                        ext = os.path.splitext(fname)[1].lower()
                        if ext in SUPPORTED_IMAGE_EXTS and fp not in self.state.files:
                            self.state.files.append(fp)
                            added.append(fp)
            if added:
                if hasattr(self, "file_panel"):
                    self.file_panel.update_list(self.state.files)
                self.log(f"📂 {len(added)} dosya eklendi (sürükle-bırak)")
                self.button_panel.set_status(f"{len(self.state.files)} dosya")
                # İlk eklenen dosyayı yükle
                self._load_file(added[0])
        except Exception as exc:
            logger.error("DnD drop hatası: %s", exc)

    # ══════════════════════════════════════════════════════════════════════════
    #  FILE MANAGEMENT
    # ══════════════════════════════════════════════════════════════════════════

    def select_files(self) -> None:
        """Dosya seçme dialogu aç — tek görsel modunda ilk dosyayı yükle."""
        paths = ask_open_files()
        if not paths:
            return
        added = 0
        for p in paths:
            if p not in self.state.files:
                self.state.files.append(p)
                added += 1
        if added:
            if hasattr(self, "file_panel"):
                self.file_panel.update_list(self.state.files)
            self.log(f"📂 {added} dosya eklendi")
            self.button_panel.set_status(f"{len(self.state.files)} dosya")
            # İlk eklenen dosyayı hemen yükle
            first_new = [p for p in paths if p in self.state.files][0]
            self._load_file(first_new)

    def _load_file(self, path: str) -> None:
        """Bir dosyayı yükle, önizlemeyi güncelle."""
        self._current_path = path
        self._current_image = None  # buffer'dan veya diskten yüklenecek
        # Buffer'da işlenmiş hali varsa onu göster
        if path in self._buffer:
            self._current_image = self._buffer[path]
            self.zoom_canvas.show_image(self._current_image, path)
            self.button_panel.set_status(f"📂 {os.path.basename(path)}")
            return
        # Yoksa arka planda diskten yükle
        def _worker():
            try:
                with Image.open(path) as img:
                    img.load()
                    img_copy = img.copy()
                self._current_image = img_copy
                self.root.after(0, lambda: self.zoom_canvas.show_image(img_copy, path))
                self.root.after(0, lambda: self.button_panel.set_status(f"📂 {os.path.basename(path)}"))
            except Exception as exc:
                logger.error("Dosya yüklenemedi: %s", exc)
                self.root.after(0, lambda: self.log(f"❌ Dosya yüklenemedi: {exc}"))
        threading.Thread(target=_worker, daemon=True).start()

    def remove_selected(self) -> None:
        """Seçili dosyayı listeden sil."""
        if hasattr(self, "file_panel"):
            idx = self.file_panel.get_selected_index()
            if idx >= 0 and idx < len(self.state.files):
                path = self.state.files[idx]
                self.state.files.pop(idx)
                self._buffer.pop(path, None)
                if self._current_path == path:
                    self._current_path = ""
                    self._current_image = None
                self.file_panel.update_list(self.state.files)
                self.log(f"🗑 Silindi: {os.path.basename(path)}")
                self.button_panel.set_save_count(len(self._buffer))
                # Sonraki dosyayı yükle
                if self.state.files:
                    self._load_file(self.state.files[min(idx, len(self.state.files)-1)])

    def select_all_files(self) -> None:
        self.file_panel.select_all()

    def deselect_all_files(self) -> None:
        self.file_panel.deselect_all()

    def on_file_selected(self, idx: int) -> None:
        """Dosya seçildiğinde önizleme güncelle ve karşılaştırma modunu sıfırla. (Req 4.6)"""
        if idx < 0 or idx >= len(self.state.files):
            return
        path = self.state.files[idx]
        # Karşılaştırma modunu sıfırla
        try:
            self.zoom_canvas.clear_after()
        except Exception:
            pass
        self._load_file(path)
        try:
            self.info_tab.update(path)
        except Exception:
            pass

    def _update_preview(self, path: str) -> None:
        """Dosyanın önizlemesini arka planda oluştur."""
        def _worker():
            try:
                if path in self._buffer:
                    img = self._buffer[path]
                    self.root.after(0, lambda: self.zoom_canvas.show_image(img))
                    return
                s = self._get_converter_state()
                preview = self.preview_engine.generate(
                    path=path,
                    width=s.get("width", self.state.width),
                    height=s.get("height", self.state.height),
                    mode=s.get("border_mode", self.state.border_mode),
                    border_color=s.get("border_color", self.state.border_color),
                    upscale=False,
                )
                self.root.after(0, lambda: self.zoom_canvas.show_image(preview))
            except Exception as exc:
                logger.error("Önizleme hatası: %s", exc)
        threading.Thread(target=_worker, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════════════
    #  CONVERT
    # ══════════════════════════════════════════════════════════════════════════

    def start_convert(self) -> None:
        """Mevcut görseli dönüştür, buffer'a yaz, önce/sonra karşılaştırmasını göster. (Req 8.1-8.5)"""
        result = self._get_current_image()
        if result is None:
            self.log("⚠️ Önce bir görsel açın")
            return
        path, img = result

        # Adım 1: Ayarları senkronize et (Req 8.1)
        self._sync_state()
        s = self._get_converter_state()

        self.log("🔄 Dönüştürme başlıyor...")
        self.button_panel.set_status("İşleniyor...")
        self.button_panel.set_progress(0.0)

        # Orijinali sakla (karşılaştırma için)
        original = img.copy()

        def _worker():
            try:
                # Adım 2: Bellekte işle (Req 8.2)
                # Undo için orijinali kaydet
                if path in self._buffer:
                    self._push_undo(path, self._buffer[path])
                converted = self._process_image(path, s)
                self._buffer[path] = converted
                # Fix #10: update _current_image on main thread via root.after
                def _update():
                    self._current_image = converted
                    self.zoom_canvas.show_comparison(original, converted)
                    self.button_panel.set_progress(1.0)
                    self.button_panel.set_save_count(len(self._buffer))
                    self.button_panel.set_status("✨ Önizleme hazır — Kaydet butonuna basın")
                    self.log(f"✅ Dönüştürüldü: {os.path.basename(path)}")
                    if hasattr(self, "file_panel"):
                        self.file_panel.set_status(path, "done")
                    if self.state.auto_save:
                        self.root.after(100, self.save_buffer)                self.root.after(0, _update)
            except Exception as exc:
                logger.error("Dönüştürme hatası: %s", exc)
                self.root.after(0, lambda: self.button_panel.set_status("❌ Dönüştürme hatası"))
                self.root.after(0, lambda: self.log(f"❌ Dönüştürme hatası: {exc}"))
                if hasattr(self, "file_panel"):
                    self.root.after(0, lambda: self.file_panel.set_status(path, "error"))

        threading.Thread(target=_worker, daemon=True).start()

    def _process_image(self, path: str, s: dict) -> Image.Image:
        """Tek bir görseli dönüştür (border + renk düzeltme)."""
        from core.smart_border import SmartBorder
        from utils.image_processor import compose_on_background

        with Image.open(path) as img:
            img.load()
            target_w = img.width if s.get("use_original_size") else s["width"]
            target_h = img.height if s.get("use_original_size") else s["height"]
            bg = SmartBorder.build(img, s["border_mode"], target_w, target_h, s["border_color"])
            composed = compose_on_background(img, bg, target_w, target_h)

        # Renk düzeltme
        es = self._get_editor_state()
        composed = ImageEditor.apply_all(
            composed,
            brightness=es.get("brightness", 1.0),
            contrast=es.get("contrast", 1.0),
            saturation=es.get("saturation", 1.0),
            sharpness=es.get("sharpness", 1.0),
        )
        return composed

    def _on_convert_done(self) -> None:
        """start_convert tamamlandığında çağrılır."""
        self.button_panel.set_status("✨ İşleme tamamlandı — Kaydet butonuna basın")
        self.button_panel.set_progress(1.0)
        self.button_panel.set_save_count(len(self._buffer))
        self.log("✨ Dönüştürme tamamlandı")
        # Seçili dosyanın önizlemesini güncelle
        idx = self.file_panel.get_selected_index()
        if 0 <= idx < len(self.state.files):
            path = self.state.files[idx]
            if path in self._buffer:
                self.zoom_canvas.show_image(self._buffer[path])

    # ══════════════════════════════════════════════════════════════════════════
    #  SAVE BUFFER
    # ══════════════════════════════════════════════════════════════════════════

    def save_buffer(self) -> None:
        """Buffer'daki görseli diske kaydet."""
        if not self._buffer:
            self.log("⚠️ Kaydedilecek görsel yok. Önce dönüştürün.")
            return

        s = self._get_converter_state()
        output_folder = s.get("output_folder", self.state.output_folder)
        fmt = s.get("format", self.state.fmt)
        quality = s.get("quality", self.state.quality)
        metadata_clean = s.get("metadata_clean", self.state.metadata_clean)
        rename_pattern = s.get("rename_pattern", self.state.rename_pattern)
        target_size_kb = s.get("target_size_kb", self.state.target_size_kb)

        self.log("💾 Kaydediliyor...")
        self.button_panel.set_status("Kaydediliyor...")

        try:
            os.makedirs(output_folder, exist_ok=True)
        except (PermissionError, OSError):
            output_folder = os.path.abspath("outputs")
            os.makedirs(output_folder, exist_ok=True)
            self.log("⚠️ Çıktı klasörü erişilemez, 'outputs/' kullanılıyor.")

        def _worker():
            try:
                os.makedirs(output_folder, exist_ok=True)
            except (PermissionError, OSError) as e:
                self.root.after(0, lambda: self.log(f"❌ Klasör oluşturulamadı: {e}"))
                return
            saved = 0
            for idx, (path, img) in enumerate(list(self._buffer.items()), start=1):
                try:
                    # rembg görselleri PNG olarak kaydedilmeli (Req 7.8, Task 13.1)
                    if path.endswith("__rembg__"):
                        save_fmt = "png"
                        actual_path = path[:-len("__rembg__")]
                        base_name = os.path.splitext(os.path.basename(actual_path))[0]
                        filename = f"{base_name}_nobg.png"
                    else:
                        save_fmt = fmt
                        filename = RenameHelper.apply(rename_pattern, path, idx, save_fmt)
                    save_path = os.path.join(output_folder, filename)
                    actual_quality = quality
                    if target_size_kb > 0 and save_fmt.lower() in ("jpg", "jpeg", "webp"):
                        actual_quality = FileSizeOptimizer.find_quality(img, target_size_kb, save_fmt)
                    self.export_engine.save_image(img, save_path, save_fmt, actual_quality, metadata_clean)
                    saved += 1
                    self.root.after(0, lambda n=os.path.basename(save_path):
                                    self.log(f"💾 Kaydedildi: {n}"))
                    if hasattr(self, "file_panel"):
                        actual_p = path[:-len("__rembg__")] if path.endswith("__rembg__") else path
                        self.root.after(0, lambda p=actual_p: self.file_panel.set_status(p, "done"))
                except Exception as exc:
                    logger.error("Kaydetme hatası %s: %s", path, exc)
                    self.root.after(0, lambda e=exc, n=os.path.basename(path):
                                    self.log(f"❌ Kaydetme hatası: {n} — {e}"))
            self.root.after(0, lambda: self._on_save_done(saved))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_save_done(self, count: int) -> None:
        self.button_panel.set_status(f"✅ {count} görsel kaydedildi")
        self.button_panel.set_progress(0.0)
        self.button_panel.set_save_count(0)
        self._buffer.clear()
        self.log(f"✅ {count} görsel kaydedildi")
        try:
            from ui.widgets.toast import Toast
            Toast.show(self.root, f"✅ {count} dosya kaydedildi")
        except Exception:
            pass
        try:
            s = self._get_converter_state()
            output_folder = s.get("output_folder", self.state.output_folder)
            self.button_panel.set_open_folder_visible(output_folder)
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    #  AI OPERATIONS
    # ══════════════════════════════════════════════════════════════════════════

    def upscale_selected(self) -> None:
        """Mevcut görseli upscale et ve önce/sonra karşılaştırmasını göster. (Req 4.1)"""
        result = self._get_current_image()
        if result is None:
            self.log("⚠️ Önce bir görsel açın")
            return
        path, img = result

        self.log("🔄 Upscale başlıyor...")
        self.button_panel.set_status("Upscale işleniyor...")
        self.button_panel.set_progress(0.0)
        self.ai_engine.set_mode(self.state.ai_mode)

        # Orijinali sakla (karşılaştırma için)
        original = img.copy()

        def _worker():
            try:
                if path in self._buffer:
                    self._push_undo(path, self._buffer[path])
                upscaled = self.ai_engine.upscale(img.copy())
                self._buffer[path] = upscaled
                # Fix #10: update _current_image on main thread
                def _update():
                    self._current_image = upscaled
                    self.zoom_canvas.show_comparison(original, upscaled)
                    self.button_panel.set_progress(1.0)
                    self.button_panel.set_save_count(len(self._buffer))
                    self.button_panel.set_status("✨ Upscale tamamlandı — Kaydet butonuna basın")
                    self.log(f"🚀 Upscale tamamlandı: {os.path.basename(path)}")
                    try:
                        from ui.widgets.toast import Toast
                        Toast.show(self.root, f"🚀 Upscale tamamlandı")
                    except Exception:
                        pass
                    if self.state.auto_save:
                        self.root.after(100, self.save_buffer)
                self.root.after(0, _update)
            except Exception as exc:
                logger.error("Upscale hatası: %s", exc)
                self.root.after(0, lambda: self.button_panel.set_status("❌ Upscale hatası"))
                self.root.after(0, lambda: self.log(f"❌ Upscale hatası: {exc}"))

        threading.Thread(target=_worker, daemon=True).start()

    def start_batch_convert(self) -> None:
        """İşaretli tüm dosyaları sırayla dönüştür."""
        files = self.file_panel.get_checked_files()
        if not files:
            self.log("⚠️ Önce dosya listesinden dosya işaretleyin")
            return
        self.state.batch_cancel = False
        self._sync_state()
        s = self._get_converter_state()
        total = len(files)
        self.log(f"🔄 Toplu dönüştürme başlıyor: {total} dosya")
        self.button_panel.set_cancel_visible(True)

        def _worker():
            for i, path in enumerate(files, start=1):
                if self.state.batch_cancel:
                    self.root.after(0, lambda: self.log("⏹ Toplu işlem iptal edildi"))
                    break
                try:
                    self.root.after(0, lambda i=i, t=total: self.button_panel.set_batch_progress(i, t))
                    self.root.after(0, lambda p=path: self.file_panel.set_status(p, "processing"))
                    converted = self._process_image(path, s)
                    self._buffer[path] = converted
                    self.root.after(0, lambda p=path: self.file_panel.set_status(p, "done"))
                except Exception as exc:
                    logger.error("Batch dönüştürme hatası %s: %s", path, exc)
                    self.root.after(0, lambda p=path: self.file_panel.set_status(p, "error"))
            self.root.after(0, lambda: self.button_panel.set_cancel_visible(False))
            self.root.after(0, lambda: self.button_panel.set_save_count(len(self._buffer)))
            self.root.after(0, lambda: self.log(f"✅ Toplu dönüştürme tamamlandı: {len(self._buffer)} dosya"))
            try:
                from ui.widgets.toast import Toast
                self.root.after(0, lambda: Toast.show(self.root, f"✅ Toplu işlem tamamlandı: {len(self._buffer)} dosya"))
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def start_batch_upscale(self) -> None:
        """İşaretli tüm dosyaları sırayla upscale et."""
        files = self.file_panel.get_checked_files()
        if not files:
            self.log("⚠️ Önce dosya listesinden dosya işaretleyin")
            return
        self.state.batch_cancel = False
        self.ai_engine.set_mode(self.state.ai_mode)
        total = len(files)
        self.log(f"🔄 Toplu upscale başlıyor: {total} dosya")
        self.button_panel.set_cancel_visible(True)

        def _worker():
            for i, path in enumerate(files, start=1):
                if self.state.batch_cancel:
                    self.root.after(0, lambda: self.log("⏹ Toplu işlem iptal edildi"))
                    break
                try:
                    self.root.after(0, lambda i=i, t=total: self.button_panel.set_batch_progress(i, t))
                    self.root.after(0, lambda p=path: self.file_panel.set_status(p, "processing"))
                    with Image.open(path) as img:
                        img.load()
                        img_copy = img.copy()
                    upscaled = self.ai_engine.upscale(img_copy)
                    self._buffer[path] = upscaled
                    self.root.after(0, lambda p=path: self.file_panel.set_status(p, "done"))
                except Exception as exc:
                    logger.error("Batch upscale hatası %s: %s", path, exc)
                    self.root.after(0, lambda p=path: self.file_panel.set_status(p, "error"))
            self.root.after(0, lambda: self.button_panel.set_cancel_visible(False))
            self.root.after(0, lambda: self.button_panel.set_save_count(len(self._buffer)))
            self.root.after(0, lambda: self.log(f"✅ Toplu upscale tamamlandı: {len(self._buffer)} dosya"))
            try:
                from ui.widgets.toast import Toast
                self.root.after(0, lambda: Toast.show(self.root, f"✅ Toplu işlem tamamlandı: {len(self._buffer)} dosya"))
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def start_batch_rembg(self) -> None:
        """İşaretli tüm dosyaların arka planını sırayla kaldır."""
        if not RemBGService.is_available():
            self.log("❌ rembg kütüphanesi bulunamadı. 'pip install rembg' komutunu çalıştırın.")
            return
        files = self.file_panel.get_checked_files()
        if not files:
            self.log("⚠️ Önce dosya listesinden dosya işaretleyin")
            return
        self.state.batch_cancel = False
        total = len(files)
        self.log(f"🔄 Toplu arka plan kaldırma başlıyor: {total} dosya")
        self.button_panel.set_cancel_visible(True)

        def _worker():
            for i, path in enumerate(files, start=1):
                if self.state.batch_cancel:
                    self.root.after(0, lambda: self.log("⏹ Toplu işlem iptal edildi"))
                    break
                try:
                    self.root.after(0, lambda i=i, t=total: self.button_panel.set_batch_progress(i, t))
                    self.root.after(0, lambda p=path: self.file_panel.set_status(p, "processing"))
                    with Image.open(path) as img:
                        img.load()
                        img_copy = img.copy()
                    removed = RemBGService.remove_background(img_copy)
                    rembg_key = path + "__rembg__"
                    self._buffer[rembg_key] = removed
                    self.root.after(0, lambda p=path: self.file_panel.set_status(p, "done"))
                except Exception as exc:
                    logger.error("Batch rembg hatası %s: %s", path, exc)
                    self.root.after(0, lambda p=path: self.file_panel.set_status(p, "error"))
            self.root.after(0, lambda: self.button_panel.set_cancel_visible(False))
            self.root.after(0, lambda: self.button_panel.set_save_count(len(self._buffer)))
            self.root.after(0, lambda: self.log(f"✅ Toplu arka plan kaldırma tamamlandı: {len(self._buffer)} dosya"))
            try:
                from ui.widgets.toast import Toast
                self.root.after(0, lambda: Toast.show(self.root, f"✅ Toplu işlem tamamlandı: {len(self._buffer)} dosya"))
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def cancel_batch(self) -> None:
        """Devam eden toplu işlemi iptal et."""
        self.state.batch_cancel = True
        self.log("⏹ İptal isteği gönderildi...")

    def remove_background_selected(self) -> None:
        """Mevcut görselin arka planını kaldır ve önce/sonra karşılaştırmasını göster. (Req 7.2-7.7)"""
        if not RemBGService.is_available():
            self.log("❌ rembg kütüphanesi bulunamadı. 'pip install rembg' komutunu çalıştırın.")
            return

        result = self._get_current_image()
        if result is None:
            self.log("⚠️ Önce bir görsel açın")
            return
        path, img = result

        self.log("🔄 Arka plan kaldırılıyor...")
        self.button_panel.set_status("Arka plan kaldırılıyor...")
        self.button_panel.set_progress(0.0)

        # Orijinali sakla (karşılaştırma için)
        original = img.copy()

        def _worker():
            try:
                if path in self._buffer:
                    self._push_undo(path, self._buffer[path])
                removed = RemBGService.remove_background(img.copy())
                # Fix #2: only store under __rembg__ key — avoids double-save and
                # prevents JPEG conversion of an RGBA image losing transparency.
                rembg_key = path + "__rembg__"
                self._buffer[rembg_key] = removed
                self._current_image = removed
                # Önce/sonra karşılaştırması göster
                self.root.after(0, lambda: self.zoom_canvas.show_comparison(original, removed))
                self.root.after(0, lambda: self.button_panel.set_progress(1.0))
                self.root.after(0, lambda: self.button_panel.set_save_count(len(self._buffer)))
                self.root.after(0, lambda: self.button_panel.set_status("✅ Arka plan kaldırıldı — Kaydet butonuna basın"))
                self.root.after(0, lambda: self.log(f"✅ Arka plan kaldırıldı: {os.path.basename(path)}"))
                try:
                    from ui.widgets.toast import Toast
                    self.root.after(0, lambda: Toast.show(self.root, "✅ Arka plan kaldırıldı", color="#9b59b6"))
                except Exception:
                    pass
                if self.state.auto_save:
                    self.root.after(100, self.save_buffer)
            except Exception as exc:
                logger.error("RemBG hatası: %s", exc)
                self.root.after(0, lambda: self.button_panel.set_status("❌ Arka plan kaldırma hatası"))
                self.root.after(0, lambda: self.log(f"❌ Arka plan kaldırma hatası: {exc}"))

        threading.Thread(target=_worker, daemon=True).start()

    def set_ai_mode_from_split(self, mode: str) -> None:
        """AI modunu değiştir ve tüm tab'lara bildir. (Req 6.5, 6.6)"""
        self.state.ai_mode = mode
        self.ai_engine.set_mode(mode)
        try:
            self.converter_tab.sync_ai_mode(mode)
        except Exception:
            pass
        try:
            self.ai_tab.sync_ai_mode(mode)
        except Exception:
            pass
        self.log(f"🤖 AI modu: {mode}")

    def _sync_state(self) -> None:
        """ConverterTab ve EditorTab'dan AppState'i güncelle. (Req 8.1, 9.4)"""
        try:
            s = self._get_converter_state()
            self.state.fmt = s.get("format", self.state.fmt)
            self.state.quality = s.get("quality", self.state.quality)
            self.state.width = s.get("width", self.state.width)
            self.state.height = s.get("height", self.state.height)
            self.state.border_mode = s.get("border_mode", self.state.border_mode)
            self.state.border_color = s.get("border_color", self.state.border_color)
            self.state.metadata_clean = s.get("metadata_clean", self.state.metadata_clean)
            self.state.output_folder = s.get("output_folder", self.state.output_folder)
            self.state.use_original_size = s.get("use_original_size", self.state.use_original_size)
            self.state.rename_pattern = s.get("rename_pattern", self.state.rename_pattern)
            self.state.target_size_kb = s.get("target_size_kb", self.state.target_size_kb)
            self.state.ai_mode = s.get("ai_mode", self.state.ai_mode)
        except Exception as exc:
            logger.warning("_sync_state hatası: %s", exc)

    def apply_language(self, lang: str = None) -> None:
        """Dil değiştiğinde tüm UI bileşenlerini güncelle."""
        try:
            from utils.i18n import t
            self.root.title(f"{APP_NAME} v{APP_VERSION}")
        except Exception:
            pass
        for tab in (self.converter_tab, self.ai_tab, self.editor_tab,
                    self.batch_tab, self.settings_tab):
            try:
                tab.apply_language()
            except Exception:
                pass

    # ══════════════════════════════════════════════════════════════════════════
    #  EDITOR OPERATIONS
    # ══════════════════════════════════════════════════════════════════════════

    def _get_current_image(self) -> Optional[tuple[str, Image.Image]]:
        """Şu an görüntülenen (path, image) çiftini döndür."""
        # Önce _current_image'ı dene (en güncel hali)
        if self._current_path and self._current_image is not None:
            return self._current_path, self._current_image.copy()
        # Sonra buffer'a bak
        if self._current_path and self._current_path in self._buffer:
            return self._current_path, self._buffer[self._current_path].copy()
        # Son çare: dosyadan oku
        if self._current_path and os.path.isfile(self._current_path):
            try:
                with Image.open(self._current_path) as img:
                    img.load()
                    return self._current_path, img.copy()
            except Exception as exc:
                self.log(f"❌ Görsel açılamadı: {exc}")
        # Eski yöntem: file_panel'den al
        if hasattr(self, "file_panel"):
            idx = self.file_panel.get_selected_index()
            if idx >= 0 and idx < len(self.state.files):
                path = self.state.files[idx]
                if path in self._buffer:
                    return path, self._buffer[path].copy()
                try:
                    with Image.open(path) as img:
                        img.load()
                        return path, img.copy()
                except Exception as exc:
                    self.log(f"❌ Görsel açılamadı: {exc}")
        return None

    def _push_undo(self, path: str, img: Image.Image) -> None:
        """Undo stack'e mevcut görseli ekle. Fix #9: max 20 entry."""
        self._undo_stack.append((path, img.copy()))
        if len(self._undo_stack) > self._MAX_UNDO:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def rotate_image(self, degrees: int) -> None:
        result = self._get_current_image()
        if result is None:
            return
        path, img = result
        self._push_undo(path, img)
        rotated = ImageEditor.rotate(img, degrees)
        self._buffer[path] = rotated
        self._current_image = rotated
        self.zoom_canvas.show_image(rotated)
        self.button_panel.set_save_count(len(self._buffer))
        self.log(f"↺ {degrees}° döndürüldü: {os.path.basename(path)}")

    def flip_image(self, direction: str) -> None:
        result = self._get_current_image()
        if result is None:
            return
        path, img = result
        self._push_undo(path, img)
        if direction == "h":
            flipped = ImageEditor.flip_horizontal(img)
            self.log(f"⇔ Yatay çevrildi: {os.path.basename(path)}")
        else:
            flipped = ImageEditor.flip_vertical(img)
            self.log(f"⇕ Dikey çevrildi: {os.path.basename(path)}")
        self._buffer[path] = flipped
        self._current_image = flipped
        self.zoom_canvas.show_image(flipped)
        self.button_panel.set_save_count(len(self._buffer))

    def start_crop_mode(self, ratio: str = "Serbest") -> None:
        """Crop mode'u aktif et — canvas sürüklemeye hazır."""
        self.zoom_canvas.enable_crop_mode(ratio=ratio)
        self.log("🔲 Kırpma modu aktif — önizleme üzerinde alan seçin")

    def apply_crop(self) -> None:
        rect = self.zoom_canvas.get_crop_rect_normalized()
        if rect is None:
            self.log("⚠️ Önizleme üzerinde kırpma alanı seçin")
            return
        result = self._get_current_image()
        if result is None:
            return
        path, img = result
        self._push_undo(path, img)
        cropped = ImageEditor.crop(img, rect)
        self._current_path = path
        self._current_image = cropped
        self._buffer[path] = cropped
        self.zoom_canvas.disable_crop_mode()
        self.zoom_canvas.show_image(cropped)
        self.state.crop_rect = rect
        self.button_panel.set_save_count(len(self._buffer))
        self.log(f"✂ Kırpıldı: {os.path.basename(path)}")
        # Editor tab'a bildir
        try:
            self.editor_tab.on_crop_applied()
        except Exception:
            pass

    def cancel_crop(self) -> None:
        self.zoom_canvas.disable_crop_mode()
        self.log("✕ Kırpma iptal edildi")
        try:
            self.editor_tab.on_crop_applied()
        except Exception:
            pass

    def apply_watermark(self) -> None:
        result = self._get_current_image()
        if result is None:
            return
        path, img = result
        es = self._get_editor_state()
        self._push_undo(path, img)

        try:
            wm_text = es.get("watermark_text", "")
            wm_logo = es.get("watermark_logo_path", "")

            if wm_logo and os.path.exists(wm_logo):
                result_img = WatermarkEngine.add_logo(
                    img,
                    logo_path=wm_logo,
                    opacity=es.get("watermark_opacity", 180),
                    position=es.get("watermark_position", "bottom-right"),
                )
            elif wm_text:
                result_img = WatermarkEngine.add_text(
                    img,
                    text=wm_text,
                    font_size=es.get("watermark_font_size", 36),
                    color=es.get("watermark_color", "#ffffff"),
                    opacity=es.get("watermark_opacity", 128),
                    position=es.get("watermark_position", "bottom-right"),
                )
            else:
                self.log("⚠️ Watermark metni veya logo seçin")
                return

            self._buffer[path] = result_img
            self._current_image = result_img
            self.zoom_canvas.show_image(result_img)
            self.button_panel.set_save_count(len(self._buffer))
            self.log(f"💧 Watermark eklendi: {os.path.basename(path)}")
        except Exception as exc:
            logger.error("Watermark hatası: %s", exc)
            self.log(f"❌ Watermark hatası: {exc}")

    def apply_filter(self, name: str) -> None:
        """Hızlı filtre uygula."""
        result = self._get_current_image()
        if result is None:
            self.log("⚠️ Önce bir görsel açın")
            return
        path, img = result
        self._push_undo(path, img)

        filter_map = {
            "grayscale": ImageEditor.apply_grayscale,
            "sepia":     ImageEditor.apply_sepia,
            "vivid":     ImageEditor.apply_vivid,
            "cool":      ImageEditor.apply_cool,
            "warm":      ImageEditor.apply_warm,
            "vintage":   ImageEditor.apply_vintage,
        }
        fn = filter_map.get(name)
        if fn is None:
            self.log(f"⚠️ Bilinmeyen filtre: {name}")
            return

        try:
            filtered = fn(img)
            self._buffer[path] = filtered
            self._current_image = filtered
            self.zoom_canvas.show_image(filtered)
            self.button_panel.set_save_count(len(self._buffer))
            self.log(f"🎨 Filtre uygulandı: {name}")
        except Exception as exc:
            logger.error("Filtre hatası: %s", exc)
            self.log(f"❌ Filtre hatası: {exc}")

    def on_settings_changed(self) -> None:
        """Ayarlar değiştiğinde mevcut görselin önizlemesini güncelle.
        Fix #11: debounce — 300ms içinde birden fazla çağrı gelirse sadece son çağrı işlenir."""
        if self._preview_debounce_id is not None:
            try:
                self.root.after_cancel(self._preview_debounce_id)
            except Exception:
                pass
        self._preview_debounce_id = self.root.after(300, self._do_update_preview)

    def _do_update_preview(self) -> None:
        """Debounce sonrası gerçek önizleme güncellemesi."""
        self._preview_debounce_id = None
        if self._current_path:
            self._update_preview(self._current_path)
        elif hasattr(self, "file_panel"):
            idx = self.file_panel.get_selected_index()
            if 0 <= idx < len(self.state.files):
                self._update_preview(self.state.files[idx])

    def undo(self) -> None:
        if not self._undo_stack:
            self.log("⚠️ Geri alınacak işlem yok")
            return
        path, img = self._undo_stack.pop()
        if path in self._buffer:
            self._redo_stack.append((path, self._buffer[path].copy()))
        self._buffer[path] = img
        self._current_image = img
        self.zoom_canvas.show_image(img)
        self.button_panel.set_save_count(len(self._buffer))
        self.log("↺ Geri alındı")

    def redo(self) -> None:
        if not self._redo_stack:
            self.log("⚠️ Yinelenecek işlem yok")
            return
        path, img = self._redo_stack.pop()
        if path in self._buffer:
            self._undo_stack.append((path, self._buffer[path].copy()))
        self._buffer[path] = img
        self._current_image = img
        self.zoom_canvas.show_image(img)
        self.button_panel.set_save_count(len(self._buffer))
        self.log("↻ Yinelendi")

    # ══════════════════════════════════════════════════════════════════════════
    #  EXPORT
    # ══════════════════════════════════════════════════════════════════════════

    def export_as_zip(self) -> None:
        """Buffer'daki görselleri ZIP olarak kaydet."""
        if not self._buffer:
            self.log("⚠️ Önce dönüştürün")
            return

        from tkinter.filedialog import asksaveasfilename
        zip_path = asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("ZIP files", "*.zip")],
            title="ZIP olarak kaydet",
        )
        if not zip_path:
            return

        s = self._get_converter_state()
        fmt = s.get("format", self.state.fmt)
        quality = s.get("quality", self.state.quality)
        rename_pattern = s.get("rename_pattern", self.state.rename_pattern)

        # Fix #3: snapshot buffer to avoid race condition and filter __rembg__ keys
        buffer_snapshot = {
            k: v for k, v in self._buffer.items()
            if not k.endswith("__rembg__")
        }

        def _worker():
            try:
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                    for idx, (path, img) in enumerate(buffer_snapshot.items(), start=1):
                        filename = RenameHelper.apply(rename_pattern, path, idx, fmt)
                        import io
                        buf = io.BytesIO()
                        pil_fmt = "JPEG" if fmt.lower() in ("jpg", "jpeg") else fmt.upper()
                        save_img = img.convert("RGB") if pil_fmt == "JPEG" and img.mode not in ("RGB", "L") else img
                        save_img.save(buf, format=pil_fmt, quality=quality)
                        zf.writestr(filename, buf.getvalue())
                self.root.after(0, lambda: self.log(f"🗜 ZIP kaydedildi: {zip_path}"))
                self.root.after(0, lambda: self.button_panel.set_status("🗜 ZIP kaydedildi"))
            except Exception as exc:
                logger.error("ZIP hatası: %s", exc)
                self.root.after(0, lambda: self.log(f"❌ ZIP hatası: {exc}"))

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def export_as_pdf(self) -> None:
        """Buffer'daki görselleri tek PDF'e birleştir."""
        if not self._buffer:
            self.log("⚠️ Önce dönüştürün")
            return

        from tkinter.filedialog import asksaveasfilename
        pdf_path = asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="PDF olarak kaydet",
        )
        if not pdf_path:
            return

        # Fix #4: snapshot buffer values before entering thread to avoid race condition
        images_snapshot = list(self._buffer.values())

        def _worker():
            try:
                images = [img.convert("RGB") for img in images_snapshot]
                if not images:
                    return
                images[0].save(
                    pdf_path,
                    save_all=True,
                    append_images=images[1:],
                )
                self.root.after(0, lambda: self.log(f"📄 PDF kaydedildi: {pdf_path}"))
                self.root.after(0, lambda: self.button_panel.set_status("📄 PDF kaydedildi"))
            except Exception as exc:
                logger.error("PDF hatası: %s", exc)
                self.root.after(0, lambda: self.log(f"❌ PDF hatası: {exc}"))

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    # ══════════════════════════════════════════════════════════════════════════
    #  WATCH MODE
    # ══════════════════════════════════════════════════════════════════════════

    def start_watch(self, folder: str) -> None:
        if not folder or not os.path.isdir(folder):
            self.log("⚠️ Geçerli bir klasör seçin")
            return
        self.state.watch_folder = folder
        self.state.watch_active = True
        self.watch_svc.start(folder)
        self.log(f"👁 İzleme başladı: {folder}")
        try:
            self.batch_tab.update_watch_status(True)
        except Exception:
            pass

    def stop_watch(self) -> None:
        self.watch_svc.stop()
        self.state.watch_active = False
        self.log("⏹ İzleme durduruldu")
        try:
            self.batch_tab.update_watch_status(False)
        except Exception:
            pass

    def _on_watch_file(self, path: str) -> None:
        """WatchService yeni dosya tespit ettiğinde çağrılır."""
        def _add():
            if path not in self.state.files:
                self.state.files.append(path)
                self.file_panel.update_list(self.state.files)
                self.log(f"👁 Yeni dosya: {os.path.basename(path)}")
                self.button_panel.set_status(f"{len(self.state.files)} dosya")
        self.root.after(0, _add)

    # ══════════════════════════════════════════════════════════════════════════
    #  MISC
    # ══════════════════════════════════════════════════════════════════════════

    def log(self, message: str) -> None:
        """Log mesajı ekle (settings tab + logger)."""
        logger.info(message)
        try:
            self.settings_tab.append_log(message)
        except Exception:
            pass
        try:
            self._topbar_status.configure(text=message[:60])
        except Exception:
            pass

    def clear_cache(self) -> None:
        """Cache klasörünü temizle."""
        import shutil
        cache_dir = "cache"
        try:
            if os.path.isdir(cache_dir):
                shutil.rmtree(cache_dir)
                os.makedirs(cache_dir, exist_ok=True)
            self.log("🗑 Önbellek temizlendi")
        except Exception as exc:
            self.log(f"❌ Önbellek temizleme hatası: {exc}")

    def _on_close(self) -> None:
        """Uygulama kapanırken ayarları kaydet."""
        try:
            if self.state.watch_active:
                self.watch_svc.stop()
        except Exception:
            pass
        self._save_settings()
        self.root.destroy()

    # ══════════════════════════════════════════════════════════════════════════
    #  HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    def _get_converter_state(self) -> dict:
        """ConverterTab'dan güncel ayarları al."""
        try:
            return self.converter_tab.get_state()
        except Exception:
            return {
                "format": self.state.fmt,
                "width": self.state.width,
                "height": self.state.height,
                "quality": self.state.quality,
                "border_mode": self.state.border_mode,
                "border_color": self.state.border_color,
                "metadata_clean": self.state.metadata_clean,
                "output_folder": self.state.output_folder,
                "use_original_size": self.state.use_original_size,
                "rename_pattern": self.state.rename_pattern,
                "target_size_kb": self.state.target_size_kb,
                "ai_mode": self.state.ai_mode,
            }

    def _get_editor_state(self) -> dict:
        """EditorTab'dan güncel renk/watermark ayarlarını al."""
        try:
            return self.editor_tab.get_editor_state()
        except Exception:
            return {
                "brightness": self.state.brightness,
                "contrast": self.state.contrast,
                "saturation": self.state.saturation,
                "sharpness": self.state.sharpness,
                "watermark_text": self.state.watermark_text,
                "watermark_font_size": self.state.watermark_font_size,
                "watermark_opacity": self.state.watermark_opacity,
                "watermark_color": self.state.watermark_color,
                "watermark_position": self.state.watermark_position,
                "watermark_logo_path": self.state.watermark_logo_path,
            }
