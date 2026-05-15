"""
EditorTab — non-destructive image editing tools.
Color correction, rotate/flip, crop, watermark.
"""

from tkinter import (
    Frame, Label, Scale, Button, Entry, Checkbutton,
    StringVar, BooleanVar, DoubleVar, IntVar,
    X, LEFT, RIGHT, BOTH, Y, HORIZONTAL, W
)
from tkinter import ttk, colorchooser, filedialog

from utils.constants import (
    C_BG_SURFACE, C_BG_RAISED, C_BG_INPUT, C_BORDER,
    C_TEXT, C_TEXT_MUTED, C_ACCENT,
)


class EditorTab(Frame):

    def __init__(self, master, controller, state):
        super().__init__(master, bg=C_BG_SURFACE)
        self.controller = controller
        self.state = state
        self._build()

    def _build(self):
        from tkinter import Canvas, Scrollbar
        sb = Scrollbar(self, orient="vertical", width=6)
        sb.pack(side=RIGHT, fill=Y)
        canvas = Canvas(self, bg=C_BG_SURFACE, highlightthickness=0,
                        yscrollcommand=sb.set)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        sb.config(command=canvas.yview)

        self.inner = Frame(canvas, bg=C_BG_SURFACE)
        win = canvas.create_window((0, 0), window=self.inner, anchor="nw")

        def _on_conf(_=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def _on_resize(e):
            canvas.itemconfig(win, width=e.width)
        def _on_scroll(e):
            if e.num == 5 or e.delta < 0:
                canvas.yview_scroll(1, "units")
            elif e.num == 4 or e.delta > 0:
                canvas.yview_scroll(-1, "units")

        self.inner.bind("<Configure>", _on_conf)
        canvas.bind("<Configure>", _on_resize)
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            canvas.bind(seq, _on_scroll)

        p = self.inner

        # ── Color correction ─────────────────────
        self._section("Renk Düzeltme")

        self.brightness_var = DoubleVar(value=self.state.brightness)
        self.contrast_var   = DoubleVar(value=self.state.contrast)
        self.saturation_var = DoubleVar(value=self.state.saturation)
        self.sharpness_var  = DoubleVar(value=self.state.sharpness)

        for label, var in [
            ("Parlaklık", self.brightness_var),
            ("Kontrast",  self.contrast_var),
            ("Doygunluk", self.saturation_var),
            ("Keskinlik", self.sharpness_var),
        ]:
            row = Frame(p, bg=C_BG_SURFACE)
            row.pack(fill=X, padx=12, pady=2)
            Label(row, text=label, bg=C_BG_SURFACE, fg=C_TEXT,
                  font=("Segoe UI", 8), width=10, anchor="w").pack(side=LEFT)
            Scale(row, variable=var, from_=0.0, to=2.0, resolution=0.05,
                  orient=HORIZONTAL, bg=C_BG_SURFACE, fg=C_TEXT,
                  troughcolor=C_BG_INPUT, highlightthickness=0, bd=0,
                  showvalue=True, font=("Segoe UI", 7),
                  command=lambda _: self._notify()
                  ).pack(side=LEFT, fill=X, expand=True)
            Button(row, text="↺", bg=C_BG_RAISED, fg=C_TEXT_MUTED,
                   relief="flat", bd=0, cursor="hand2", font=("Segoe UI", 9),
                   command=lambda v=var: (v.set(1.0), self._notify())
                   ).pack(side=LEFT, padx=(4, 0))

        Button(p, text="Tümünü Sıfırla", command=self._reset_colors,
               bg=C_BG_RAISED, fg=C_TEXT_MUTED, relief="flat", bd=0,
               cursor="hand2", font=("Segoe UI", 8)
               ).pack(anchor=W, padx=12, pady=(4, 8))

        # ── Rotate / Flip ────────────────────────
        Frame(p, bg=C_BORDER, height=1).pack(fill=X, padx=12, pady=8)
        self._section("Döndür / Çevir")

        rot_row = Frame(p, bg=C_BG_SURFACE)
        rot_row.pack(fill=X, padx=12, pady=(0, 4))
        for text, cmd in [
            ("↺ 90°",  lambda: self.controller.rotate_image(90)),
            ("↻ 90°",  lambda: self.controller.rotate_image(-90)),
            ("180°",   lambda: self.controller.rotate_image(180)),
            ("⇔ Yatay", lambda: self.controller.flip_image("h")),
            ("⇕ Dikey", lambda: self.controller.flip_image("v")),
        ]:
            Button(rot_row, text=text, command=cmd,
                   bg=C_BG_RAISED, fg=C_TEXT, relief="flat", bd=0,
                   cursor="hand2", font=("Segoe UI", 8), padx=6, pady=4
                   ).pack(side=LEFT, padx=2)

        # ── Crop ────────────────────────────────
        Frame(p, bg=C_BORDER, height=1).pack(fill=X, padx=12, pady=8)
        self._section("Kırpma")

        self._crop_hint_lbl = Label(
            p, text="● Kırpma modu kapalı",
            bg=C_BG_SURFACE, fg=C_TEXT_MUTED, font=("Segoe UI", 8), anchor="w",
        )
        self._crop_hint_lbl.pack(fill=X, padx=12, pady=(0, 4))

        crop_ratio_row = Frame(p, bg=C_BG_SURFACE)
        crop_ratio_row.pack(fill=X, padx=12, pady=(0, 4))
        Label(crop_ratio_row, text="Oran:", bg=C_BG_SURFACE, fg=C_TEXT_MUTED,
              font=("Segoe UI", 8)).pack(side=LEFT, padx=(0, 4))
        self._crop_ratio_var = StringVar(value="Serbest")
        from tkinter import ttk as _ttk
        crop_ratio_combo = _ttk.Combobox(
            crop_ratio_row, textvariable=self._crop_ratio_var,
            values=["Serbest", "1:1", "4:3", "16:9", "9:16", "3:2", "2:3"],
            state="readonly", width=10,
        )
        crop_ratio_combo.pack(side=LEFT)

        crop_btns = Frame(p, bg=C_BG_SURFACE)
        crop_btns.pack(fill=X, padx=12, pady=(0, 4))

        self._crop_select_btn = Button(
            crop_btns, text="🔲 Alan Seç",
            command=self._start_crop_mode,
            bg=C_BG_RAISED, fg=C_TEXT, relief="flat", bd=0,
            cursor="hand2", font=("Segoe UI", 9, "bold"), padx=10, pady=4,
        )
        self._crop_select_btn.pack(side=LEFT, padx=(0, 4))

        self._crop_apply_btn = Button(
            crop_btns, text="✂ Uygula",
            command=self.controller.apply_crop,
            bg=C_ACCENT, fg="#000000", relief="flat", bd=0,
            cursor="hand2", font=("Segoe UI", 9, "bold"), padx=10, pady=4,
            state="disabled",
        )
        self._crop_apply_btn.pack(side=LEFT, padx=(0, 4))

        Button(
            crop_btns, text="✕ İptal",
            command=self._cancel_crop_mode,
            bg=C_BG_RAISED, fg=C_TEXT, relief="flat", bd=0,
            cursor="hand2", font=("Segoe UI", 9), padx=8, pady=4,
        ).pack(side=LEFT)

        # ── Hızlı Filtreler ──────────────────────────
        Frame(p, bg=C_BORDER, height=1).pack(fill=X, padx=12, pady=8)
        self._section("Hızlı Filtreler")

        filters_grid = Frame(p, bg=C_BG_SURFACE)
        filters_grid.pack(fill=X, padx=12, pady=(0, 8))

        filter_defs = [
            ("⬛ Siyah-Beyaz", "grayscale"),
            ("🟤 Sepya",       "sepia"),
            ("🌈 Canlı",       "vivid"),
            ("❄ Soğuk",       "cool"),
            ("🔥 Sıcak",       "warm"),
            ("📷 Vintage",     "vintage"),
        ]

        for i, (label, fname) in enumerate(filter_defs):
            col = i % 2
            row_idx = i // 2
            btn = Button(
                filters_grid, text=label,
                command=lambda f=fname: self.controller.apply_filter(f),
                bg=C_BG_RAISED, fg=C_TEXT,
                relief="flat", bd=0, cursor="hand2",
                font=("Segoe UI", 8), padx=6, pady=4,
            )
            btn.grid(row=row_idx, column=col, padx=2, pady=2, sticky="ew")

        filters_grid.columnconfigure(0, weight=1)
        filters_grid.columnconfigure(1, weight=1)

        # ── Watermark ────────────────────────────
        Frame(p, bg=C_BORDER, height=1).pack(fill=X, padx=12, pady=8)
        self._section("Watermark")

        # Text watermark
        Label(p, text="Metin", bg=C_BG_SURFACE, fg=C_TEXT_MUTED,
              font=("Segoe UI", 7, "bold"), anchor="w"
              ).pack(fill=X, padx=12, pady=(4, 2))
        self.wm_text_var = StringVar(value=self.state.watermark_text)
        Entry(p, textvariable=self.wm_text_var,
              bg=C_BG_INPUT, fg=C_TEXT, relief="flat", bd=0,
              highlightthickness=1, highlightbackground=C_BORDER,
              insertbackground=C_TEXT, font=("Segoe UI", 9)
              ).pack(fill=X, padx=12, pady=(0, 4), ipady=4)

        # Font size + opacity
        wm_row = Frame(p, bg=C_BG_SURFACE)
        wm_row.pack(fill=X, padx=12, pady=(0, 4))
        Label(wm_row, text="Boyut", bg=C_BG_SURFACE, fg=C_TEXT_MUTED,
              font=("Segoe UI", 8)).pack(side=LEFT)
        self.wm_size_var = IntVar(value=self.state.watermark_font_size)
        Scale(wm_row, variable=self.wm_size_var, from_=8, to=120,
              orient=HORIZONTAL, bg=C_BG_SURFACE, fg=C_TEXT,
              troughcolor=C_BG_INPUT, highlightthickness=0, bd=0,
              showvalue=True, font=("Segoe UI", 7)
              ).pack(side=LEFT, fill=X, expand=True, padx=(4, 12))
        Label(wm_row, text="Opaklık", bg=C_BG_SURFACE, fg=C_TEXT_MUTED,
              font=("Segoe UI", 8)).pack(side=LEFT)
        self.wm_opacity_var = IntVar(value=self.state.watermark_opacity)
        Scale(wm_row, variable=self.wm_opacity_var, from_=0, to=255,
              orient=HORIZONTAL, bg=C_BG_SURFACE, fg=C_TEXT,
              troughcolor=C_BG_INPUT, highlightthickness=0, bd=0,
              showvalue=True, font=("Segoe UI", 7)
              ).pack(side=LEFT, fill=X, expand=True)

        # Color + position
        wm_row2 = Frame(p, bg=C_BG_SURFACE)
        wm_row2.pack(fill=X, padx=12, pady=(0, 4))
        self.wm_color = self.state.watermark_color
        self.wm_color_btn = Button(
            wm_row2, text="🎨 Renk", bg=self.wm_color, fg=C_TEXT,
            relief="flat", bd=0, cursor="hand2", font=("Segoe UI", 8),
            command=self._pick_wm_color,
        )
        self.wm_color_btn.pack(side=LEFT, padx=(0, 8))

        self.wm_pos_var = StringVar(value=self.state.watermark_position)
        pos_combo = ttk.Combobox(
            wm_row2, textvariable=self.wm_pos_var,
            values=["top-left", "top-right", "bottom-left", "bottom-right", "center"],
            state="readonly", width=14,
        )
        pos_combo.pack(side=LEFT)

        # Logo watermark
        Label(p, text="Logo (PNG)", bg=C_BG_SURFACE, fg=C_TEXT_MUTED,
              font=("Segoe UI", 7, "bold"), anchor="w"
              ).pack(fill=X, padx=12, pady=(8, 2))
        logo_row = Frame(p, bg=C_BG_SURFACE)
        logo_row.pack(fill=X, padx=12, pady=(0, 4))
        self.wm_logo_var = StringVar(value=self.state.watermark_logo_path)
        Entry(logo_row, textvariable=self.wm_logo_var,
              bg=C_BG_INPUT, fg=C_TEXT, relief="flat", bd=0,
              highlightthickness=1, highlightbackground=C_BORDER,
              insertbackground=C_TEXT, font=("Segoe UI", 8)
              ).pack(side=LEFT, fill=X, expand=True, ipady=4)
        Button(logo_row, text="📁", bg=C_BG_RAISED, fg=C_TEXT,
               relief="flat", bd=0, cursor="hand2", font=("Segoe UI Emoji", 10),
               command=self._pick_logo).pack(side=LEFT, padx=(4, 0))

        # Apply watermark button
        Button(p, text="💧 Watermark Uygula", command=self.controller.apply_watermark,
               bg=C_ACCENT, fg="#000000", relief="flat", bd=0,
               cursor="hand2", font=("Segoe UI", 9, "bold"), pady=6
               ).pack(fill=X, padx=12, pady=(8, 4))

        Frame(p, bg=C_BG_SURFACE, height=16).pack()

    def _start_crop_mode(self):
        try:
            ratio = self._crop_ratio_var.get() if hasattr(self, "_crop_ratio_var") else "Serbest"
            self.controller.start_crop_mode(ratio=ratio)
        except Exception:
            pass
        self._crop_hint_lbl.configure(
            text="● Önizleme üzerinde alan sürükleyin", fg="#f0a500"
        )
        self._crop_select_btn.configure(bg="#f0a500", fg="#000000")
        self._crop_apply_btn.configure(state="normal")

    def _cancel_crop_mode(self):
        try:
            self.controller.cancel_crop()
        except Exception:
            pass
        self._crop_hint_lbl.configure(text="● Kırpma modu kapalı", fg=C_TEXT_MUTED)
        self._crop_select_btn.configure(bg=C_BG_RAISED, fg=C_TEXT)
        self._crop_apply_btn.configure(state="disabled")

    def on_crop_applied(self):
        self._crop_hint_lbl.configure(text="● Kırpma modu kapalı", fg=C_TEXT_MUTED)
        self._crop_select_btn.configure(bg=C_BG_RAISED, fg=C_TEXT)
        self._crop_apply_btn.configure(state="disabled")

    def _reset_colors(self):
        for var in (self.brightness_var, self.contrast_var,
                    self.saturation_var, self.sharpness_var):
            var.set(1.0)
        self._notify()

    def _pick_wm_color(self):
        color = colorchooser.askcolor(initialcolor=self.wm_color)
        if color and color[1]:
            self.wm_color = color[1]
            self.wm_color_btn.configure(bg=self.wm_color)

    def _pick_logo(self):
        path = filedialog.askopenfilename(
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if path:
            self.wm_logo_var.set(path)

    def _notify(self):
        try:
            self.controller.on_settings_changed()
        except Exception:
            pass

    def get_editor_state(self) -> dict:
        return {
            "brightness":            self.brightness_var.get(),
            "contrast":              self.contrast_var.get(),
            "saturation":            self.saturation_var.get(),
            "sharpness":             self.sharpness_var.get(),
            "watermark_text":        self.wm_text_var.get(),
            "watermark_font_size":   self.wm_size_var.get(),
            "watermark_opacity":     self.wm_opacity_var.get(),
            "watermark_color":       self.wm_color,
            "watermark_position":    self.wm_pos_var.get(),
            "watermark_logo_path":   self.wm_logo_var.get(),
        }

    def _section(self, text):
        Label(self.inner, text=text.upper(), bg=C_BG_SURFACE, fg=C_TEXT_MUTED,
              font=("Segoe UI", 7, "bold"), anchor="w"
              ).pack(fill=X, padx=12, pady=(12, 3))

    def apply_language(self) -> None:
        pass  # EditorTab etiketleri şu an Türkçe sabit; i18n gerekirse buraya eklenebilir

    def apply_theme(self, panel_bg, element_bg, border_color, text_color):
        self.configure(bg=panel_bg)
        try:
            self.inner.configure(bg=panel_bg)
        except Exception:
            pass
        self._theme_recursive(self.inner, panel_bg, element_bg, border_color, text_color)

    def _theme_recursive(self, widget, panel_bg, element_bg, border_color, text_color):
        try:
            cls = widget.winfo_class()
            if cls == "Frame":
                widget.configure(bg=panel_bg)
            elif cls == "Label":
                widget.configure(bg=panel_bg, fg=text_color)
            elif cls == "Entry":
                widget.configure(bg=element_bg, fg=text_color,
                                 highlightbackground=border_color,
                                 insertbackground=text_color)
            elif cls == "Scale":
                widget.configure(bg=panel_bg, fg=text_color, troughcolor=element_bg)
            elif cls == "Button":
                # wm_color_btn'i koru — kullanıcı renk seçimi
                if hasattr(self, "wm_color_btn") and widget is self.wm_color_btn:
                    widget.configure(fg=text_color)
                else:
                    widget.configure(bg=element_bg, fg=text_color,
                                     activebackground=border_color)
            elif cls == "Checkbutton":
                widget.configure(bg=panel_bg, fg=text_color,
                                 activebackground=panel_bg, selectcolor=element_bg)
        except Exception:
            pass
        for child in widget.winfo_children():
            self._theme_recursive(child, panel_bg, element_bg, border_color, text_color)
