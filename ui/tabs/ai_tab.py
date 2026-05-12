"""
AITab — AI tools panel.
Upscale, background removal, denoise (future), face enhance (future).
"""

from tkinter import Frame, Label, Button, X, LEFT, RIGHT, BOTH, Y
from tkinter import ttk
from utils.constants import (
    C_BG_SURFACE, C_BG_RAISED, C_BG_INPUT, C_BORDER,
    C_TEXT, C_TEXT_MUTED, C_ACCENT, C_ACCENT_ALT, C_ACCENT_PUR,
)
from utils.i18n import t


class AITab(Frame):

    def __init__(self, master, controller, state):
        super().__init__(master, bg=C_BG_SURFACE)
        self.controller = controller
        self.state = state
        self._build()

    def _build(self):
        p = self

        # ── Header ──────────────────────────────
        self._header_lbl = Label(p, text=t("ai_tools").upper(), bg=C_BG_SURFACE, fg=C_TEXT_MUTED,
              font=("Segoe UI", 8, "bold"), anchor="w")
        self._header_lbl.pack(fill=X, padx=14, pady=(14, 4))
        Frame(p, bg=C_BORDER, height=1).pack(fill=X, padx=12)

        # ── AI Mode ─────────────────────────────
        self._ai_mode_lbl = Label(p, text=t("ai_mode").upper(), bg=C_BG_SURFACE, fg=C_TEXT_MUTED,
              font=("Segoe UI", 7, "bold"), anchor="w")
        self._ai_mode_lbl.pack(fill=X, padx=14, pady=(14, 4))

        from tkinter import StringVar
        self.ai_mode_var = StringVar(value=self.state.ai_mode)
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Dark.TCombobox",
                        fieldbackground=C_BG_INPUT, background=C_BG_INPUT,
                        foreground=C_TEXT, bordercolor=C_BORDER,
                        arrowcolor=C_TEXT_MUTED, selectbackground=C_BG_INPUT,
                        selectforeground=C_TEXT)
        self.ai_combo = ttk.Combobox(
            p, textvariable=self.ai_mode_var,
            values=["low", "balanced", "ultra"],
            state="readonly", style="Dark.TCombobox",
        )
        self.ai_combo.pack(fill=X, padx=12, pady=(0, 4), ipady=3)
        self.ai_combo.bind("<<ComboboxSelected>>",
                           lambda *_: self.controller.set_ai_mode_from_split(self.ai_mode_var.get()))

        # Mode descriptions
        mode_info = Frame(p, bg=C_BG_RAISED)
        mode_info.pack(fill=X, padx=12, pady=(0, 12))
        self._mode_label = Label(mode_info, text=self._mode_desc("low"),
                                 bg=C_BG_RAISED, fg=C_TEXT_MUTED,
                                 font=("Segoe UI", 8), anchor="w", wraplength=260, justify="left")
        self._mode_label.pack(fill=X, padx=8, pady=6)
        self.ai_combo.bind("<<ComboboxSelected>>", self._on_mode_change)

        # ── Upscale ─────────────────────────────
        self._upscale_card = self._tool_card(
            p,
            icon="🚀",
            title="AI Upscale",
            desc=t("upscale"),
            btn_text=t("upscale"),
            btn_color=C_ACCENT_ALT,
            command=self.controller.upscale_selected,
        )

        # ── Background removal ───────────────────
        self._rembg_card = self._tool_card(
            p,
            icon="🪄",
            title=t("remove_bg"),
            desc="rembg + u2net",
            btn_text=t("remove_bg"),
            btn_color=C_ACCENT_PUR,
            command=self.controller.remove_background_selected,
        )

        # ── Coming soon ──────────────────────────
        self._coming_soon(p, "🔇", "Denoise", "Soon")
        self._coming_soon(p, "👤", "Face Enhance", "Soon")

    def _on_mode_change(self, _=None):
        mode = self.ai_mode_var.get()
        self._mode_label.configure(text=self._mode_desc(mode))
        self.controller.set_ai_mode_from_split(mode)

    @staticmethod
    def _mode_desc(mode: str) -> str:
        from utils.i18n import get_language
        lang = get_language()
        if lang == "en":
            descs = {
                "low":      "🔵 Low — Fast, CPU friendly. Small ONNX model.",
                "balanced": "🟡 Balanced — Better quality. Moderate speed.",
                "ultra":    "🔴 Ultra — Best quality. May be slow.",
            }
        else:
            descs = {
                "low":      "🔵 Low — Hızlı, CPU dostu. Küçük ONNX modeli.",
                "balanced": "🟡 Balanced — Dengeli kalite. Daha iyi sonuç.",
                "ultra":    "🔴 Ultra — En yüksek kalite. Yavaş olabilir.",
            }
        return descs.get(mode, "")

    def _tool_card(self, master, icon, title, desc, btn_text, btn_color, command):
        card = Frame(master, bg=C_BG_RAISED)
        card.pack(fill=X, padx=12, pady=6)

        top = Frame(card, bg=C_BG_RAISED)
        top.pack(fill=X, padx=10, pady=(10, 4))

        Label(top, text=icon, bg=C_BG_RAISED, fg=C_TEXT,
              font=("Segoe UI Emoji", 18)).pack(side=LEFT, padx=(0, 8))

        info = Frame(top, bg=C_BG_RAISED)
        info.pack(side=LEFT, fill=X, expand=True)
        Label(info, text=title, bg=C_BG_RAISED, fg=C_TEXT,
              font=("Segoe UI", 10, "bold"), anchor="w").pack(fill=X)
        Label(info, text=desc, bg=C_BG_RAISED, fg=C_TEXT_MUTED,
              font=("Segoe UI", 8), anchor="w", wraplength=200, justify="left").pack(fill=X)

        btn = Button(card, text=btn_text, command=command,
                     bg=btn_color, fg="#000000",
                     activebackground=btn_color, activeforeground="#000000",
                     relief="flat", bd=0, font=("Segoe UI", 9, "bold"),
                     cursor="hand2", pady=6)
        btn.pack(fill=X, padx=10, pady=(4, 10))
        return card

    def _coming_soon(self, master, icon, title, badge):
        card = Frame(master, bg=C_BG_RAISED)
        card.pack(fill=X, padx=12, pady=6)
        row = Frame(card, bg=C_BG_RAISED)
        row.pack(fill=X, padx=10, pady=10)
        Label(row, text=icon, bg=C_BG_RAISED, fg=C_TEXT_MUTED,
              font=("Segoe UI Emoji", 16)).pack(side=LEFT, padx=(0, 8))
        Label(row, text=title, bg=C_BG_RAISED, fg=C_TEXT_MUTED,
              font=("Segoe UI", 10)).pack(side=LEFT)
        Label(row, text=badge, bg=C_BG_RAISED, fg=C_TEXT_MUTED,
              font=("Segoe UI", 8)).pack(side=RIGHT)

    def sync_ai_mode(self, mode: str):
        self.ai_mode_var.set(mode)
        self._mode_label.configure(text=self._mode_desc(mode))

    def apply_language(self) -> None:
        """Refresh all translatable labels."""
        try:
            self._header_lbl.configure(text=t("ai_tools").upper())
        except Exception:
            pass
        try:
            self._ai_mode_lbl.configure(text=t("ai_mode").upper())
        except Exception:
            pass
        try:
            self._mode_label.configure(text=self._mode_desc(self.ai_mode_var.get()))
        except Exception:
            pass
        # Rebuild tool cards is complex; just update button texts via winfo_children
        for card in (getattr(self, "_upscale_card", None),
                     getattr(self, "_rembg_card", None)):
            if card is None:
                continue
            for child in card.winfo_children():
                try:
                    if child.winfo_class() == "Button":
                        cur = child.cget("text")
                        if "Upscale" in cur or cur in ("🚀  AI Upscale", "🚀  Upscale"):
                            child.configure(text=t("upscale"))
                        elif "Arka" in cur or "Remove" in cur or "BG" in cur:
                            child.configure(text=t("remove_bg"))
                except Exception:
                    pass

    def apply_theme(self, panel_bg, element_bg, border_color, text_color):
        self.configure(bg=panel_bg)
        # Header ve mode label'ları
        for attr in ("_header_lbl", "_ai_mode_lbl"):
            lbl = getattr(self, attr, None)
            if lbl:
                try:
                    lbl.configure(bg=panel_bg, fg=text_color)
                except Exception:
                    pass
        # mode_info Frame ve _mode_label
        try:
            self._mode_label.master.configure(bg=element_bg)
        except Exception:
            pass
        try:
            self._mode_label.configure(bg=element_bg, fg=text_color)
        except Exception:
            pass
        # _upscale_card ve _rembg_card — recursive güncelle
        def _update_card(widget):
            try:
                cls = widget.winfo_class()
                if cls == "Frame":
                    widget.configure(bg=element_bg)
                elif cls == "Label":
                    widget.configure(bg=element_bg, fg=text_color)
                elif cls == "Button":
                    pass  # renkli butonları koru
            except Exception:
                pass
            for child in widget.winfo_children():
                _update_card(child)

        for card_attr in ("_upscale_card", "_rembg_card"):
            card = getattr(self, card_attr, None)
            if card:
                _update_card(card)
        # _coming_soon kartları — tüm Frame/Label'ları güncelle
        for child in self.winfo_children():
            try:
                cls = child.winfo_class()
                if cls == "Frame" and child not in (
                    getattr(self, "_upscale_card", None),
                    getattr(self, "_rembg_card", None),
                ):
                    # coming soon kartı olabilir
                    _update_card(child)
            except Exception:
                pass
        # ttk.Combobox style güncelle
        from tkinter import ttk
        style = ttk.Style()
        style.configure("Dark.TCombobox",
                        fieldbackground=element_bg, background=element_bg,
                        foreground=text_color, bordercolor=border_color,
                        arrowcolor=text_color, selectbackground=element_bg,
                        selectforeground=text_color)
        try:
            self.ai_combo.configure(style="Dark.TCombobox")
        except Exception:
            pass
