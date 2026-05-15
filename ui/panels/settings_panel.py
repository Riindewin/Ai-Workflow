"""
SettingsPanel — right sidebar, scrollable settings form.

Layout (top → bottom inside right_panel):
  ┌──────────────────┐
  │  ⚙ AYARLAR       │  ← fixed header
  ├──────────────────┤
  │  scrollable form │  ← expand=True
  └──────────────────┘
"""

from tkinter import (
    Frame, Canvas, Scrollbar, Label, Entry, Scale,
    Button, Checkbutton, StringVar, BooleanVar,
    W, X, HORIZONTAL, RIGHT, LEFT, BOTH, Y,
)
from tkinter import ttk

from ui.dialogs.picker_dialogs import ask_directory, ask_color
from utils.constants import (
    C_BG_SURFACE, C_BG_RAISED, C_BG_INPUT, C_BG_HOVER,
    C_BORDER, C_TEXT, C_TEXT_MUTED, C_ACCENT,
    L_BG_SURFACE, L_BG_RAISED, L_BG_INPUT, L_TEXT,
)


class SettingsPanel:

    def __init__(self, master, controller, state):
        self.controller = controller
        self.state = state

        self.frame = Frame(master, bg=C_BG_SURFACE)

        # ── Fixed header ────────────────────────
        header = Frame(self.frame, bg=C_BG_SURFACE, height=44)
        header.pack(fill=X)
        header.pack_propagate(False)

        Label(
            header,
            text="AYARLAR",
            bg=C_BG_SURFACE,
            fg=C_TEXT_MUTED,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).pack(side=LEFT, padx=14)

        Frame(self.frame, bg=C_BORDER, height=1).pack(fill=X)

        # ── Scrollable body ─────────────────────
        body = Frame(self.frame, bg=C_BG_SURFACE)
        body.pack(fill=BOTH, expand=True)

        self._scrollbar = Scrollbar(body, orient="vertical", width=6)
        self._scrollbar.pack(side=RIGHT, fill=Y)

        self.canvas = Canvas(
            body,
            bg=C_BG_SURFACE,
            highlightthickness=0,
            yscrollcommand=self._scrollbar.set,
        )
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        self._scrollbar.config(command=self.canvas.yview)

        self.inner = Frame(self.canvas, bg=C_BG_SURFACE)
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", self._on_configure)
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.canvas.bind(seq, self._on_scroll)
            self.inner.bind(seq, self._on_scroll)

        self._build()

    # ── Scroll helpers ───────────────────────────

    def _on_configure(self, _=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_resize(self, event):
        self.canvas.itemconfig(self._win, width=event.width)

    def _on_scroll(self, event):
        if event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")

    # ── Form builder ─────────────────────────────

    def _build(self):
        self.format_var       = StringVar(value=self.state.fmt)
        self.width_var        = StringVar(value=str(self.state.width))
        self.height_var       = StringVar(value=str(self.state.height))
        self.border_mode_var  = StringVar(value=self.state.border_mode)
        self.metadata_var     = BooleanVar(value=self.state.metadata_clean)
        self.ai_mode_var      = StringVar(value=self.state.ai_mode)
        self.original_size_var = BooleanVar(value=getattr(self.state, "use_original_size", False))

        p = self.inner  # shorthand

        # Format
        self._section("Format")
        self.format_combo = self._combo(p, self.format_var, ["jpg", "png", "webp", "bmp"],
                                        command=lambda *_: self.controller.on_settings_changed())

        # Dimensions
        self._section("Boyut")

        # Orijinal boyut checkbox (5.1)
        self.original_size_check = self._check(
            p, "Orijinal Boyutu Koru", self.original_size_var,
            command=self._on_original_size_toggle,
        )

        dim_row = Frame(p, bg=C_BG_SURFACE)
        dim_row.pack(fill=X, padx=12, pady=(0, 4))
        Label(dim_row, text="W", bg=C_BG_SURFACE, fg=C_TEXT_MUTED,
              font=("Segoe UI", 8)).pack(side=LEFT, padx=(0, 4))
        self.width_entry = self._entry_inline(dim_row, self.width_var)
        Label(dim_row, text="H", bg=C_BG_SURFACE, fg=C_TEXT_MUTED,
              font=("Segoe UI", 8)).pack(side=LEFT, padx=(8, 4))
        self.height_entry = self._entry_inline(dim_row, self.height_var)

        # Apply initial state for original_size
        if self.original_size_var.get():
            self.width_entry.configure(state="disabled")
            self.height_entry.configure(state="disabled")

        # Quality (5.3)
        self._section("Kalite")
        q_row = Frame(p, bg=C_BG_SURFACE)
        q_row.pack(fill=X, padx=12, pady=(0, 4))
        self.quality = Scale(
            q_row, from_=1, to=100, orient=HORIZONTAL,
            bg=C_BG_SURFACE, fg=C_TEXT, troughcolor=C_BG_INPUT,
            highlightthickness=0, bd=0, showvalue=True,
            font=("Segoe UI", 8),
            command=lambda _: self.controller.on_settings_changed(),
        )
        self.quality.set(self.state.quality)
        self.quality.pack(fill=X, expand=True)

        # Border mode (5.2)
        self._section("Kenarlık Modu")
        self.border_combo = self._combo(
            p, self.border_mode_var, ["normal", "blur", "dominant"],
            command=lambda *_: self.controller.on_settings_changed(),
        )

        # Border colour (5.4)
        self._section("Kenarlık Rengi")
        self.color_btn = Button(
            p,
            text="  Renk Seç",
            bg=self.state.border_color,
            fg=C_TEXT,
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 9),
            command=self._choose_color,
            anchor="w",
        )
        self.color_btn.pack(fill=X, padx=12, pady=(0, 4))

        # Output folder (5.6)
        self._section("Çıktı Klasörü")
        folder_row = Frame(p, bg=C_BG_SURFACE)
        folder_row.pack(fill=X, padx=12, pady=(0, 4))
        self.folder_entry = Entry(
            folder_row,
            bg=C_BG_INPUT, fg=C_TEXT,
            relief="flat", bd=0,
            highlightthickness=1, highlightbackground=C_BORDER,
            insertbackground=C_TEXT,
            font=("Segoe UI", 8),
        )
        self.folder_entry.insert(0, self.state.output_folder)
        self.folder_entry.pack(side=LEFT, fill=X, expand=True, ipady=4)

        Button(
            folder_row,
            text="📁",
            bg=C_BG_RAISED, fg=C_TEXT,
            relief="flat", bd=0,
            cursor="hand2",
            font=("Segoe UI Emoji", 10),
            command=self._choose_folder,
        ).pack(side=LEFT, padx=(4, 0))

        # AI mode (5.7)
        self._section("AI Modu")
        self.ai_combo = self._combo(
            p, self.ai_mode_var, ["low", "balanced", "ultra"],
            command=lambda *_: self.controller.on_settings_changed(),
        )

        # Checkboxes (5.5)
        Frame(p, bg=C_BORDER, height=1).pack(fill=X, padx=12, pady=10)

        self.meta_check = self._check(p, "Metadata Temizle", self.metadata_var)

        # Bottom padding
        Frame(p, bg=C_BG_SURFACE, height=16).pack()

    # ── Widget factories ─────────────────────────

    def _section(self, text: str):
        Label(
            self.inner,
            text=text.upper(),
            bg=C_BG_SURFACE,
            fg=C_TEXT_MUTED,
            font=("Segoe UI", 7, "bold"),
            anchor="w",
        ).pack(fill=X, padx=12, pady=(12, 3))

    def _combo(self, master, var, values, command=None):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "Dark.TCombobox",
            fieldbackground=C_BG_INPUT,
            background=C_BG_INPUT,
            foreground=C_TEXT,
            bordercolor=C_BORDER,
            arrowcolor=C_TEXT_MUTED,
            selectbackground=C_BG_INPUT,
            selectforeground=C_TEXT,
        )
        cb = ttk.Combobox(
            master,
            textvariable=var,
            values=values,
            state="readonly",
            style="Dark.TCombobox",
        )
        cb.pack(fill=X, padx=12, pady=(0, 4), ipady=3)
        if command:
            cb.bind("<<ComboboxSelected>>", command)
        return cb

    def _entry_inline(self, master, var):
        e = Entry(
            master,
            textvariable=var,
            bg=C_BG_INPUT, fg=C_TEXT,
            relief="flat", bd=0,
            highlightthickness=1, highlightbackground=C_BORDER,
            insertbackground=C_TEXT,
            font=("Segoe UI", 9),
            width=6,
        )
        e.pack(side=LEFT, ipady=4)
        return e

    def _check(self, master, text, var, command=None):
        kw = {"command": command} if command else {}
        cb = Checkbutton(
            master,
            text=text,
            variable=var,
            bg=C_BG_SURFACE,
            fg=C_TEXT,
            activebackground=C_BG_SURFACE,
            activeforeground=C_TEXT,
            selectcolor=C_BG_INPUT,
            bd=0,
            font=("Segoe UI", 9),
            anchor="w",
            **kw,
        )
        cb.pack(fill=X, padx=12, pady=2)
        return cb

    # ── Callbacks ────────────────────────────────

    def _on_original_size_toggle(self) -> None:
        """5.1 — disable/enable W/H entries based on checkbox state."""
        state = "disabled" if self.original_size_var.get() else "normal"
        self.width_entry.configure(state=state)
        self.height_entry.configure(state=state)
        self.controller.on_settings_changed()

    def _choose_folder(self):
        folder = ask_directory()
        if not folder:
            return
        self.folder_entry.delete(0, "end")
        self.folder_entry.insert(0, folder)
        self.state.output_folder = folder
        self.controller.on_settings_changed()

    def _choose_color(self):
        color = ask_color(self.state.border_color)
        if not color:
            return
        self.state.border_color = color  # 5.4 — write to state.border_color
        self.color_btn.configure(bg=color)
        self.controller.on_settings_changed()

    # ── Public API ───────────────────────────────

    def get_state(self) -> dict:
        return {
            "format":           self.format_var.get(),
            "width":            int(self.width_var.get() or 1500),
            "height":           int(self.height_var.get() or 1500),
            "quality":          self.quality.get(),
            "border_mode":      self.border_mode_var.get(),
            "metadata_clean":   self.metadata_var.get(),
            "output_folder":    self.folder_entry.get(),
            "border_color":     self.state.border_color,
            "ai_mode":          self.ai_mode_var.get(),
            "preview_upscale":  False,
            "use_original_size": self.original_size_var.get(),  # 9 — new key
        }

    def sync_ai_mode(self, mode: str) -> None:
        """5.7 — sync AI mode combobox from external source (SplitButton)."""
        self.ai_mode_var.set(mode)

    # ── Theme (5.8) ──────────────────────────────

    def apply_theme(self, panel_bg, element_bg, border_color, text_color):
        self.frame.configure(bg=panel_bg)
        self.canvas.configure(bg=panel_bg)
        self.inner.configure(bg=panel_bg)

        # Reconfigure ttk.Style for both dark and light variants
        style = ttk.Style()
        style.configure(
            "Dark.TCombobox",
            fieldbackground=element_bg,
            background=element_bg,
            foreground=text_color,
            bordercolor=border_color,
            arrowcolor=text_color,
            selectbackground=element_bg,
            selectforeground=text_color,
        )
        style.map(
            "Dark.TCombobox",
            fieldbackground=[("readonly", element_bg)],
            foreground=[("readonly", text_color)],
            selectbackground=[("readonly", element_bg)],
            selectforeground=[("readonly", text_color)],
        )

        def _try(w, **kw):
            try:
                w.configure(**kw)
            except Exception:
                pass

        # Walk all children and update colours
        for child in self.inner.winfo_children():
            _try(child, bg=panel_bg)
            try:
                child_type = child.winfo_class()
            except Exception:
                child_type = ""

            if child_type == "Label":
                _try(child, bg=panel_bg, fg=text_color)
            elif child_type == "Checkbutton":
                _try(child, bg=panel_bg, fg=text_color,
                     activebackground=panel_bg, activeforeground=text_color,
                     selectcolor=element_bg)
            elif child_type == "Button":
                _try(child, bg=element_bg, fg=text_color,
                     activebackground=border_color, activeforeground=text_color)
            elif child_type == "Frame":
                _try(child, bg=panel_bg)
                for sub in child.winfo_children():
                    sub_type = sub.winfo_class()
                    if sub_type == "Label":
                        _try(sub, bg=panel_bg, fg=text_color)
                    elif sub_type == "Entry":
                        _try(sub, bg=element_bg, fg=text_color,
                             highlightbackground=border_color,
                             insertbackground=text_color)
                    elif sub_type == "Button":
                        _try(sub, bg=element_bg, fg=text_color,
                             activebackground=border_color, activeforeground=text_color)
                    else:
                        _try(sub, bg=panel_bg)

        # Explicitly update known Entry widgets (5.8)
        for entry in (self.width_entry, self.height_entry, self.folder_entry):
            _try(entry, bg=element_bg, fg=text_color,
                 highlightbackground=border_color,
                 insertbackground=text_color)

        # Update quality Scale
        _try(self.quality, bg=panel_bg, fg=text_color, troughcolor=element_bg)

        # Update combobox style on all combos
        for cb in (self.format_combo, self.border_combo, self.ai_combo):
            _try(cb, style="Dark.TCombobox")
