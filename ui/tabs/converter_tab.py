"""
ConverterTab — image conversion settings panel.
Format, dimensions, border, quality, presets.
"""

from tkinter import (
    Frame, Label, Entry, Scale, Button, Checkbutton,
    StringVar, BooleanVar, IntVar, X, LEFT, RIGHT, BOTH, Y, HORIZONTAL, W
)
from tkinter import ttk

from ui.dialogs.picker_dialogs import ask_color
from utils.constants import (
    SUPPORTED_FORMATS, SUPPORTED_BORDER_MODES, PRESET_TEMPLATES,
    C_BG_SURFACE, C_BG_INPUT, C_BG_RAISED, C_BORDER,
    C_TEXT, C_TEXT_MUTED, C_ACCENT,
)
from utils.i18n import t


class ConverterTab(Frame):

    def __init__(self, master, controller, state):
        super().__init__(master, bg=C_BG_SURFACE)
        self.controller = controller
        self.state = state
        self._combo_widgets: list = []
        self._aspect_locked = False
        self._aspect_ratio = 1.0
        self._updating_dims = False
        self._build()

    def _build(self):
        from tkinter import Canvas, Scrollbar
        # Scrollable inner
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
            self.inner.bind(seq, _on_scroll)

        p = self.inner

        # ── Preset ──────────────────────────────
        self._section_preset = self._section(t("preset"))
        preset_row = Frame(p, bg=C_BG_SURFACE)
        preset_row.pack(fill=X, padx=12, pady=(0, 4))

        self.preset_var = StringVar(value=t("custom"))
        preset_names = [t("custom")] + list(PRESET_TEMPLATES.keys())
        self.preset_combo = self._combo(preset_row, self.preset_var, preset_names)
        self.preset_combo.pack(side=LEFT, fill=X, expand=True)
        self.preset_combo.bind("<<ComboboxSelected>>", self._on_preset_selected)

        Button(preset_row, text="💾", bg=C_BG_RAISED, fg=C_TEXT,
               relief="flat", bd=0, cursor="hand2", font=("Segoe UI Emoji", 11),
               command=self._save_preset).pack(side=LEFT, padx=(4, 0))

        self._delete_preset_btn = Button(
            preset_row, text="✕",
            bg=C_BG_RAISED, fg="#e05555",
            relief="flat", bd=0, cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            command=self._delete_preset,
        )
        self._delete_preset_btn.pack(side=LEFT, padx=(2, 0))

        # ── Format ──────────────────────────────
        self._section_format = self._section(t("format"))
        self.format_var = StringVar(value=self.state.fmt)
        self.format_combo = self._combo(p, self.format_var, SUPPORTED_FORMATS,
                                        command=lambda *_: self._notify())
        self.format_combo.pack(fill=X, padx=12, pady=(0, 4))

        # ── Dimensions ──────────────────────────
        self._section_size = self._section(t("size"))
        self.original_size_var = BooleanVar(value=self.state.use_original_size)
        self._orig_size_chk = self._check(p, t("keep_original_size"), self.original_size_var,
                    command=self._on_original_toggle)

        dim_row = Frame(p, bg=C_BG_SURFACE)
        dim_row.pack(fill=X, padx=12, pady=(0, 4))
        Label(dim_row, text="W", bg=C_BG_SURFACE, fg=C_TEXT_MUTED,
              font=("Segoe UI", 8)).pack(side=LEFT, padx=(0, 4))
        self.width_var = StringVar(value=str(self.state.width))
        self.width_entry = self._entry_sm(dim_row, self.width_var)
        Label(dim_row, text="H", bg=C_BG_SURFACE, fg=C_TEXT_MUTED,
              font=("Segoe UI", 8)).pack(side=LEFT, padx=(8, 4))
        self.height_var = StringVar(value=str(self.state.height))
        self.height_entry = self._entry_sm(dim_row, self.height_var)

        # Aspect ratio kilit butonu
        self._lock_btn = Button(
            dim_row, text="🔓",
            bg=C_BG_RAISED, fg=C_TEXT_MUTED,
            relief="flat", bd=0, cursor="hand2",
            font=("Segoe UI", 10),
            command=self._toggle_aspect_lock,
        )
        self._lock_btn.pack(side=LEFT, padx=(4, 0))

        if self.original_size_var.get():
            self.width_entry.configure(state="disabled")
            self.height_entry.configure(state="disabled")

        # ── Quality ─────────────────────────────
        self._section_quality = self._section(t("quality"))
        self.quality_var = IntVar(value=self.state.quality)
        self.quality_scale = Scale(
            p, from_=1, to=100, orient=HORIZONTAL, variable=self.quality_var,
            bg=C_BG_SURFACE, fg=C_TEXT, troughcolor=C_BG_INPUT,
            highlightthickness=0, bd=0, showvalue=True, font=("Segoe UI", 8),
            command=lambda _: self._notify(),
        )
        self.quality_scale.pack(fill=X, padx=12, pady=(0, 4))

        # ── Target file size ────────────────────
        self._section_target = self._section(t("target_size"))
        size_row = Frame(p, bg=C_BG_SURFACE)
        size_row.pack(fill=X, padx=12, pady=(0, 4))
        self.target_size_var = StringVar(value=str(self.state.target_size_kb or ""))
        Entry(size_row, textvariable=self.target_size_var,
              bg=C_BG_INPUT, fg=C_TEXT, relief="flat", bd=0,
              highlightthickness=1, highlightbackground=C_BORDER,
              insertbackground=C_TEXT, font=("Segoe UI", 9), width=8,
              ).pack(side=LEFT, ipady=4)
        self._target_size_unit_lbl = Label(
            size_row,
            text="KB  (0 = " + ("devre dışı" if t("custom") == "Özel" else "disabled") + ")",
            bg=C_BG_SURFACE, fg=C_TEXT_MUTED, font=("Segoe UI", 8),
        )
        self._target_size_unit_lbl.pack(side=LEFT, padx=6)

        # ── Border ──────────────────────────────
        self._section_border_mode = self._section(t("border_mode"))
        self.border_mode_var = StringVar(value=self.state.border_mode)
        self._combo(p, self.border_mode_var, SUPPORTED_BORDER_MODES,
                    command=lambda *_: self._notify()).pack(fill=X, padx=12, pady=(0, 4))

        self._section_border_color = self._section(t("border_color"))
        self.color_btn = Button(
            p, text="  " + t("border_color"), bg=self.state.border_color, fg=C_TEXT,
            relief="flat", bd=0, cursor="hand2", font=("Segoe UI", 9),
            command=self._choose_color, anchor="w",
        )
        self.color_btn.pack(fill=X, padx=12, pady=(0, 4))

        # ── Output folder ───────────────────────
        self._section_folder = self._section(t("output_folder"))
        from ui.dialogs.picker_dialogs import ask_directory
        folder_row = Frame(p, bg=C_BG_SURFACE)
        folder_row.pack(fill=X, padx=12, pady=(0, 4))
        self.folder_var = StringVar(value=self.state.output_folder)
        self.folder_entry = Entry(
            folder_row, textvariable=self.folder_var,
            bg=C_BG_INPUT, fg=C_TEXT, relief="flat", bd=0,
            highlightthickness=1, highlightbackground=C_BORDER,
            insertbackground=C_TEXT, font=("Segoe UI", 8),
        )
        self.folder_entry.pack(side=LEFT, fill=X, expand=True, ipady=4)
        Button(folder_row, text="📁", bg=C_BG_RAISED, fg=C_TEXT,
               relief="flat", bd=0, cursor="hand2", font=("Segoe UI Emoji", 10),
               command=lambda: self._pick_folder(ask_directory)).pack(side=LEFT, padx=(4, 0))

        # ── Rename pattern ──────────────────────
        self._section_rename = self._section(t("filename_pattern"))
        self.rename_var = StringVar(value=self.state.rename_pattern)
        rename_entry = Entry(
            p, textvariable=self.rename_var,
            bg=C_BG_INPUT, fg=C_TEXT, relief="flat", bd=0,
            highlightthickness=1, highlightbackground=C_BORDER,
            insertbackground=C_TEXT, font=("Segoe UI", 9),
        )
        rename_entry.pack(fill=X, padx=12, pady=(0, 2), ipady=4)
        Label(p, text="{name} {date} {index} {index:03d} {ext}",
              bg=C_BG_SURFACE, fg=C_TEXT_MUTED, font=("Segoe UI", 7)
              ).pack(anchor=W, padx=12)

        # ── Metadata ────────────────────────────
        Frame(p, bg=C_BORDER, height=1).pack(fill=X, padx=12, pady=10)
        self.metadata_var = BooleanVar(value=self.state.metadata_clean)
        self._metadata_chk = self._check(p, t("metadata_clean"), self.metadata_var)

        Frame(p, bg=C_BG_SURFACE, height=16).pack()

    # ── Aspect Ratio ─────────────────────────────

    def _toggle_aspect_lock(self) -> None:
        """Aspect ratio kilidini aç/kapat."""
        self._aspect_locked = not self._aspect_locked
        if self._aspect_locked:
            # Mevcut oranı kaydet
            try:
                w = int(self.width_var.get() or 1)
                h = int(self.height_var.get() or 1)
                self._aspect_ratio = w / h if h > 0 else 1.0
            except (ValueError, ZeroDivisionError):
                self._aspect_ratio = 1.0
            self._lock_btn.configure(text="🔒", fg=C_ACCENT)
            # Trace ekle
            self.width_var.trace_add("write", self._on_width_change)
            self.height_var.trace_add("write", self._on_height_change)
        else:
            self._lock_btn.configure(text="🔓", fg=C_TEXT_MUTED)
            # Trace'leri kaldır
            try:
                self.width_var.trace_remove("write",
                    self.width_var.trace_info()[0][1])
            except Exception:
                pass
            try:
                self.height_var.trace_remove("write",
                    self.height_var.trace_info()[0][1])
            except Exception:
                pass

    def _on_width_change(self, *args) -> None:
        """W değişince H'yi otomatik hesapla."""
        if self._updating_dims or not self._aspect_locked:
            return
        try:
            w = int(self.width_var.get())
            h = round(w / self._aspect_ratio)
            self._updating_dims = True
            self.height_var.set(str(h))
            self._updating_dims = False
        except (ValueError, ZeroDivisionError):
            self._updating_dims = False

    def _on_height_change(self, *args) -> None:
        """H değişince W'yi otomatik hesapla."""
        if self._updating_dims or not self._aspect_locked:
            return
        try:
            h = int(self.height_var.get())
            w = round(h * self._aspect_ratio)
            self._updating_dims = True
            self.width_var.set(str(w))
            self._updating_dims = False
        except (ValueError, ZeroDivisionError):
            self._updating_dims = False

    # ── Callbacks ────────────────────────────────

    def _on_preset_selected(self, _=None):
        name = self.preset_var.get()
        if name == t("custom"):
            return
        data = PRESET_TEMPLATES.get(name)
        if not data:
            # Try user preset
            try:
                data = self.controller.preset_svc.get(name)
            except Exception:
                return
        if data:
            if "width" in data:
                self.width_var.set(str(data["width"]))
            if "height" in data:
                self.height_var.set(str(data["height"]))
            if "format" in data:
                self.format_var.set(data["format"])
            if "quality" in data:
                self.quality_var.set(data["quality"])
            self._notify()

    def _save_preset(self):
        from tkinter.simpledialog import askstring
        name = askstring(t("save_preset"), t("preset_name"))
        if not name:
            return
        self.controller.preset_svc.save_user(name, self.get_state())
        self._refresh_preset_list()
        self.controller.log(f"{t('preset_saved')}: {name}")

    def _delete_preset(self) -> None:
        """Seçili kullanıcı preset'ini sil."""
        from tkinter import messagebox
        name = self.preset_var.get()
        if name == t("custom") or name in PRESET_TEMPLATES:
            messagebox.showwarning("Sil", "Yerleşik preset'ler silinemez.")
            return
        if messagebox.askyesno("Preset Sil", f'"{name}" preset\'ini silmek istiyor musunuz?'):
            try:
                self.controller.preset_svc.delete_user(name)
                self._refresh_preset_list()
                self.preset_var.set(t("custom"))
                self.controller.log(f"🗑 Preset silindi: {name}")
            except Exception as exc:
                messagebox.showerror("Hata", f"Preset silinemedi: {exc}")

    def _refresh_preset_list(self) -> None:
        """Preset combo listesini yenile."""
        try:
            user_presets = self.controller.preset_svc.list_user()
        except Exception:
            user_presets = []
        all_presets = [t("custom")] + list(PRESET_TEMPLATES.keys()) + user_presets
        self.preset_combo.configure(values=all_presets)

    def _on_original_toggle(self):
        state = "disabled" if self.original_size_var.get() else "normal"
        self.width_entry.configure(state=state)
        self.height_entry.configure(state=state)
        self._notify()

    def _choose_color(self):
        color = ask_color(self.state.border_color)
        if color:
            self.state.border_color = color
            self.color_btn.configure(bg=color)
            self._notify()

    def _pick_folder(self, ask_fn):
        folder = ask_fn()
        if folder:
            self.folder_var.set(folder)
            self.state.output_folder = folder
            self._notify()

    def _notify(self):
        try:
            self.controller.on_settings_changed()
        except Exception:
            pass

    # ── Public API ───────────────────────────────

    def get_state(self) -> dict:
        try:
            w = int(self.width_var.get() or 1500)
        except ValueError:
            w = 1500
        try:
            h = int(self.height_var.get() or 1500)
        except ValueError:
            h = 1500
        try:
            ts = int(self.target_size_var.get() or 0)
        except ValueError:
            ts = 0
        return {
            "format":           self.format_var.get(),
            "width":            w,
            "height":           h,
            "quality":          self.quality_var.get(),
            "border_mode":      self.border_mode_var.get(),
            "border_color":     self.state.border_color,
            "metadata_clean":   self.metadata_var.get(),
            "output_folder":    self.folder_var.get(),
            "use_original_size": self.original_size_var.get(),
            "rename_pattern":   self.rename_var.get(),
            "target_size_kb":   ts,
            "preview_upscale":  False,
            "ai_mode":          self.state.ai_mode,
        }

    def sync_ai_mode(self, mode: str):
        self.state.ai_mode = mode

    def apply_theme(self, panel_bg, element_bg, border_color, text_color):
        self.configure(bg=panel_bg)
        self._theme_children(self.inner, panel_bg, element_bg, border_color, text_color)
        style = ttk.Style()
        style.configure("Dark.TCombobox",
            fieldbackground=element_bg, background=element_bg,
            foreground=text_color, bordercolor=border_color,
            arrowcolor=text_color, selectbackground=element_bg,
            selectforeground=text_color)
        style.map("Dark.TCombobox",
            fieldbackground=[("readonly", element_bg)],
            foreground=[("readonly", text_color)],
            selectbackground=[("readonly", element_bg)],
            selectforeground=[("readonly", text_color)])
        for cb in self._combo_widgets:
            try:
                cb.configure(style="Dark.TCombobox")
            except Exception:
                pass

    def _theme_children(self, widget, panel_bg, element_bg, border_color, text_color):
        from tkinter import Entry as TkEntry, Label as TkLabel, Checkbutton as TkCheck
        from tkinter import Button as TkBtn, Frame as TkFrame, Scale as TkScale
        try:
            cls = widget.winfo_class()
        except Exception:
            return
        try:
            if cls in ("Frame",):
                widget.configure(bg=panel_bg)
            elif cls == "Label":
                widget.configure(bg=panel_bg, fg=text_color)
            elif cls == "Entry":
                widget.configure(bg=element_bg, fg=text_color,
                                 highlightbackground=border_color,
                                 insertbackground=text_color)
            elif cls == "Checkbutton":
                widget.configure(bg=panel_bg, fg=text_color,
                                 activebackground=panel_bg, selectcolor=element_bg)
            elif cls == "Scale":
                widget.configure(bg=panel_bg, fg=text_color, troughcolor=element_bg)
            elif cls == "Button":
                widget.configure(bg=element_bg, fg=text_color,
                                 activebackground=border_color)
        except Exception:
            pass
        for child in widget.winfo_children():
            self._theme_children(child, panel_bg, element_bg, border_color, text_color)

    # ── Widget factories ─────────────────────────

    def _section(self, text) -> Label:
        lbl = Label(self.inner, text=text.upper(), bg=C_BG_SURFACE, fg=C_TEXT_MUTED,
                    font=("Segoe UI", 7, "bold"), anchor="w")
        lbl.pack(fill=X, padx=12, pady=(12, 3))
        return lbl

    def apply_language(self) -> None:
        """Refresh all translatable labels."""
        _map = {
            "_section_preset":       "preset",
            "_section_format":       "format",
            "_section_size":         "size",
            "_section_quality":      "quality",
            "_section_target":       "target_size",
            "_section_border_mode":  "border_mode",
            "_section_border_color": "border_color",
            "_section_folder":       "output_folder",
            "_section_rename":       "filename_pattern",
        }
        for attr, key in _map.items():
            lbl = getattr(self, attr, None)
            if lbl:
                try:
                    lbl.configure(text=t(key).upper())
                except Exception:
                    pass
        try:
            self._orig_size_chk.configure(text=t("keep_original_size"))
        except Exception:
            pass
        try:
            self._metadata_chk.configure(text=t("metadata_clean"))
        except Exception:
            pass
        try:
            lang = t("custom")
            cur = self.preset_var.get()
            # If currently showing a localized "custom" label, update it
            if cur in ("Özel", "Custom"):
                self.preset_var.set(lang)
            self.preset_combo.configure(values=[lang] + list(PRESET_TEMPLATES.keys()))
        except Exception:
            pass
        try:
            disabled_txt = "devre dışı" if t("custom") == "Özel" else "disabled"
            self._target_size_unit_lbl.configure(text=f"KB  (0 = {disabled_txt})")
        except Exception:
            pass

    def _combo(self, master, var, values, command=None):
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
        cb = ttk.Combobox(master, textvariable=var, values=values,
                          state="readonly", style="Dark.TCombobox")
        if command:
            cb.bind("<<ComboboxSelected>>", command)
        self._combo_widgets.append(cb)
        return cb

    def _entry_sm(self, master, var):
        e = Entry(master, textvariable=var, bg=C_BG_INPUT, fg=C_TEXT,
                  relief="flat", bd=0, highlightthickness=1,
                  highlightbackground=C_BORDER, insertbackground=C_TEXT,
                  font=("Segoe UI", 9), width=6)
        e.pack(side=LEFT, ipady=4)
        return e

    def _check(self, master, text, var, command=None):
        kw = {"command": command} if command else {}
        cb = Checkbutton(master, text=text, variable=var,
                         bg=C_BG_SURFACE, fg=C_TEXT,
                         activebackground=C_BG_SURFACE, activeforeground=C_TEXT,
                         selectcolor=C_BG_INPUT, bd=0, font=("Segoe UI", 9),
                         anchor="w", **kw)
        cb.pack(fill=X, padx=12, pady=2)
        return cb
