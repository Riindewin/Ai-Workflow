"""
BatchTab — batch processing, export options, watch mode.
"""

from tkinter import (
    Frame, Label, Button, Entry, Checkbutton,
    StringVar, BooleanVar, X, LEFT, RIGHT, BOTH, Y, W
)

from utils.constants import (
    C_BG_SURFACE, C_BG_RAISED, C_BG_INPUT, C_BORDER,
    C_TEXT, C_TEXT_MUTED, C_ACCENT, C_ACCENT_ORG,
    RENAME_PATTERNS,
)
from utils.i18n import t


class BatchTab(Frame):

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

        # ── Batch actions ────────────────────────
        self._batch_section_lbl = self._section(t("batch_ops"))

        # Fix #12: _action_btn now returns the Button widget
        self._convert_all_btn = self._action_btn(p, t("convert_all"),
                         self.controller.start_batch_convert, C_ACCENT)
        self._upscale_all_btn = self._action_btn(p, t("upscale_all"),
                         self.controller.start_batch_upscale, "#00a8ff")
        self._rembg_all_btn = self._action_btn(p, t("remove_bg_all"),
                         self.controller.start_batch_rembg, "#9b59b6")

        # ── Export ───────────────────────────────
        Frame(p, bg=C_BORDER, height=1).pack(fill=X, padx=12, pady=10)
        self._export_section_lbl = self._section(t("export"))

        self._save_all_btn = self._action_btn(p, t("save_all"),
                         self.controller.save_buffer, "#27ae60")
        self._zip_btn = self._action_btn(p, t("export_zip"),
                         self.controller.export_as_zip, C_ACCENT_ORG)
        self._pdf_btn = self._action_btn(p, t("export_pdf"),
                         self.controller.export_as_pdf, "#e74c3c")

        # ── Watch mode ───────────────────────────
        Frame(p, bg=C_BORDER, height=1).pack(fill=X, padx=12, pady=10)
        self._watch_section_lbl = self._section(t("watch_mode"))

        self._watch_folder_lbl = Label(p, text=t("watch_folder"), bg=C_BG_SURFACE, fg=C_TEXT_MUTED,
              font=("Segoe UI", 8), anchor="w")
        self._watch_folder_lbl.pack(fill=X, padx=12, pady=(0, 2))

        watch_row = Frame(p, bg=C_BG_SURFACE)
        watch_row.pack(fill=X, padx=12, pady=(0, 4))
        self.watch_var = StringVar(value=self.state.watch_folder)
        Entry(watch_row, textvariable=self.watch_var,
              bg=C_BG_INPUT, fg=C_TEXT, relief="flat", bd=0,
              highlightthickness=1, highlightbackground=C_BORDER,
              insertbackground=C_TEXT, font=("Segoe UI", 8)
              ).pack(side=LEFT, fill=X, expand=True, ipady=4)

        from ui.dialogs.picker_dialogs import ask_directory
        Button(watch_row, text="📁", bg=C_BG_RAISED, fg=C_TEXT,
               relief="flat", bd=0, cursor="hand2", font=("Segoe UI Emoji", 10),
               command=lambda: self._pick_watch(ask_directory)
               ).pack(side=LEFT, padx=(4, 0))

        self.watch_active_var = BooleanVar(value=self.state.watch_active)
        self.watch_toggle_btn = Button(
            p,
            text="▶  İzlemeyi Başlat",
            command=self._toggle_watch,
            bg=C_BG_RAISED, fg=C_TEXT,
            relief="flat", bd=0, cursor="hand2",
            font=("Segoe UI", 9, "bold"), pady=6,
        )
        self.watch_toggle_btn.pack(fill=X, padx=12, pady=(0, 4))

        self.watch_status = Label(p, text="● Pasif", bg=C_BG_SURFACE,
                                  fg=C_TEXT_MUTED, font=("Segoe UI", 8), anchor="w")
        self.watch_status.pack(fill=X, padx=12)

        Frame(p, bg=C_BG_SURFACE, height=16).pack()

    def _pick_watch(self, ask_fn):
        folder = ask_fn()
        if folder:
            self.watch_var.set(folder)

    def _toggle_watch(self):
        if self.state.watch_active:
            self.controller.stop_watch()
            self.watch_toggle_btn.configure(text="▶  İzlemeyi Başlat", bg=C_BG_RAISED)
            self.watch_status.configure(text="● Pasif", fg=C_TEXT_MUTED)
        else:
            folder = self.watch_var.get()
            if not folder:
                self.controller.log("⚠️ İzlenecek klasör seçin")
                return
            self.controller.start_watch(folder)
            self.watch_toggle_btn.configure(text="⏹  İzlemeyi Durdur", bg="#e05555")
            self.watch_status.configure(text="● Aktif — izleniyor", fg=C_ACCENT)

    def update_watch_status(self, active: bool):
        self.state.watch_active = active
        if active:
            self.watch_toggle_btn.configure(text="⏹  İzlemeyi Durdur", bg="#e05555")
            self.watch_status.configure(text="● Aktif — izleniyor", fg=C_ACCENT)
        else:
            self.watch_toggle_btn.configure(text="▶  İzlemeyi Başlat", bg=C_BG_RAISED)
            self.watch_status.configure(text="● Pasif", fg=C_TEXT_MUTED)

    # Fix #12: return the Button so callers can reference it
    def _action_btn(self, master, text, command, color) -> Button:
        btn = Button(master, text=text, command=command,
               bg=color, fg="#000000",
               activebackground=color, activeforeground="#000000",
               relief="flat", bd=0, cursor="hand2",
               font=("Segoe UI", 9, "bold"), pady=7)
        btn.pack(fill=X, padx=12, pady=3)
        return btn

    def _section(self, text) -> Label:
        lbl = Label(self.inner, text=text.upper(), bg=C_BG_SURFACE, fg=C_TEXT_MUTED,
              font=("Segoe UI", 7, "bold"), anchor="w")
        lbl.pack(fill=X, padx=12, pady=(12, 3))
        return lbl

    # Fix #33: added apply_language so dil değişikliği batch tab'ı da günceller
    def apply_language(self) -> None:
        try:
            self._batch_section_lbl.configure(text=t("batch_ops").upper())
        except Exception:
            pass
        try:
            self._export_section_lbl.configure(text=t("export").upper())
        except Exception:
            pass
        try:
            self._watch_section_lbl.configure(text=t("watch_mode").upper())
        except Exception:
            pass
        try:
            self._watch_folder_lbl.configure(text=t("watch_folder"))
        except Exception:
            pass
        _btn_map = [
            ("_convert_all_btn", "convert_all"),
            ("_upscale_all_btn", "upscale_all"),
            ("_rembg_all_btn",   "remove_bg_all"),
            ("_save_all_btn",    "save_all"),
            ("_zip_btn",         "export_zip"),
            ("_pdf_btn",         "export_pdf"),
        ]
        for attr, key in _btn_map:
            btn = getattr(self, attr, None)
            if btn:
                try:
                    btn.configure(text=t(key))
                except Exception:
                    pass

    def apply_theme(self, panel_bg, element_bg, border_color, text_color):
        self.configure(bg=panel_bg)
        try:
            self.inner.configure(bg=panel_bg)
        except Exception:
            pass
        # Tüm inner widget'larını güncelle
        for child in self.inner.winfo_children():
            try:
                cls = child.winfo_class()
                if cls == "Frame":
                    child.configure(bg=panel_bg)
                elif cls == "Label":
                    child.configure(bg=panel_bg, fg=text_color)
                elif cls == "Entry":
                    child.configure(bg=element_bg, fg=text_color,
                                    highlightbackground=border_color,
                                    insertbackground=text_color)
                elif cls == "Button":
                    # watch_toggle_btn aktif/pasif rengini koru
                    if hasattr(self, "watch_toggle_btn") and child is self.watch_toggle_btn:
                        if self.state.watch_active:
                            pass  # aktif rengi koru (#e05555)
                        else:
                            child.configure(bg=element_bg, fg=text_color)
                    else:
                        child.configure(bg=element_bg, fg=text_color)
            except Exception:
                pass
        # Section label'larını güncelle
        for attr in ("_batch_section_lbl", "_export_section_lbl",
                     "_watch_section_lbl", "_watch_folder_lbl", "watch_status"):
            lbl = getattr(self, attr, None)
            if lbl:
                try:
                    lbl.configure(bg=panel_bg, fg=text_color)
                except Exception:
                    pass
