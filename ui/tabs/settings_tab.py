"""
SettingsTab — theme selector, language selector, log, cache, about.
"""

from tkinter import (
    Frame, Label, Button, Checkbutton, BooleanVar, StringVar,
    Text, Scrollbar, X, Y, LEFT, RIGHT, BOTH, BOTTOM, END
)
from tkinter import ttk
from utils.themes import ThemePalette, ALL_THEMES, DARK
from utils.i18n import t, get_language, set_language, register_change_callback, unregister_change_callback


class SettingsTab(Frame):

    def __init__(self, master, controller, state):
        super().__init__(master, bg=DARK.bg_surface)
        self.controller = controller
        self.state = state
        self._palette = DARK
        self._log_visible = False
        self._log_messages: list[str] = []
        self._build()
        register_change_callback(self._on_lang_change)

    def destroy(self):
        unregister_change_callback(self._on_lang_change)
        super().destroy()

    def _build(self):
        from tkinter import Canvas, Scrollbar as SB
        sb = SB(self, orient="vertical", width=6)
        sb.pack(side=RIGHT, fill=Y)
        self._canvas = Canvas(self, bg=DARK.bg_surface, highlightthickness=0,
                              yscrollcommand=sb.set)
        self._canvas.pack(side=LEFT, fill=BOTH, expand=True)
        sb.config(command=self._canvas.yview)

        self.inner = Frame(self._canvas, bg=DARK.bg_surface)
        self._win = self._canvas.create_window((0, 0), window=self.inner, anchor="nw")

        def _on_conf(_=None):
            self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        def _on_resize(e):
            self._canvas.itemconfig(self._win, width=e.width)
        def _on_scroll(e):
            if e.num == 5 or e.delta < 0:
                self._canvas.yview_scroll(1, "units")
            elif e.num == 4 or e.delta > 0:
                self._canvas.yview_scroll(-1, "units")

        self.inner.bind("<Configure>", _on_conf)
        self._canvas.bind("<Configure>", _on_resize)
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self._canvas.bind(seq, _on_scroll)

        p = self.inner

        # ── Language selector ────────────────────
        self._lang_section_lbl = self._section(t("language"))
        lang_row = Frame(p, bg=DARK.bg_surface)
        lang_row.pack(fill=X, padx=12, pady=(0, 8))

        self._lang_var = StringVar(value=get_language())
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Dark.TCombobox",
                        fieldbackground=DARK.bg_input, background=DARK.bg_input,
                        foreground=DARK.text, bordercolor=DARK.border,
                        arrowcolor=DARK.text_muted, selectbackground=DARK.bg_input,
                        selectforeground=DARK.text)
        self._lang_combo = ttk.Combobox(
            lang_row,
            textvariable=self._lang_var,
            values=["tr", "en"],
            state="readonly",
            style="Dark.TCombobox",
            width=10,
        )
        self._lang_combo.pack(side=LEFT, ipady=3)
        self._lang_combo.bind("<<ComboboxSelected>>", self._on_lang_selected)

        # Language display labels next to combo
        self._lang_hint = Label(
            lang_row,
            text="🇹🇷 Türkçe / 🇬🇧 English",
            bg=DARK.bg_surface, fg=DARK.text_muted,
            font=("Segoe UI", 8),
        )
        self._lang_hint.pack(side=LEFT, padx=8)

        # ── Theme selector ───────────────────────
        Frame(p, bg=DARK.border, height=1).pack(fill=X, padx=12, pady=8)
        self._theme_section_lbl = self._section(t("theme"))
        theme_grid = Frame(p, bg=DARK.bg_surface)
        theme_grid.pack(fill=X, padx=12, pady=(0, 8))

        self._theme_btns: dict = {}
        for theme_name, palette in ALL_THEMES.items():
            card = self._make_theme_card(theme_grid, palette)
            card.pack(fill=X, pady=2)
            self._theme_btns[theme_name] = card

        self._highlight_active_theme()

        # ── Log ─────────────────────────────────
        Frame(p, bg=DARK.border, height=1).pack(fill=X, padx=12, pady=8)
        self._log_section_lbl = self._section(t("activity_log"))

        self.log_toggle_btn = Button(
            p, text=t("show_log"),
            command=self._toggle_log,
            bg=DARK.bg_raised, fg=DARK.text,
            relief="flat", bd=0, cursor="hand2",
            font=("Segoe UI", 9), pady=6,
        )
        self.log_toggle_btn.pack(fill=X, padx=12, pady=(0, 4))

        # Log slide-in panel (hidden by default)
        self._log_panel = Frame(p, bg=DARK.bg_input)
        self._log_sb = Scrollbar(self._log_panel, orient="vertical", width=5)
        self._log_sb.pack(side=RIGHT, fill=Y)
        self._log_text = Text(
            self._log_panel,
            bg=DARK.bg_input, fg=DARK.log_fg,
            relief="flat", bd=0, highlightthickness=0,
            font=("Consolas", 8), wrap="word", height=10,
            yscrollcommand=self._log_sb.set,
            state="disabled",
        )
        self._log_text.pack(side=LEFT, fill=BOTH, expand=True)
        self._log_sb.config(command=self._log_text.yview)

        # ── Auto-remove ──────────────────────────
        Frame(p, bg=DARK.border, height=1).pack(fill=X, padx=12, pady=8)
        self._filelist_section_lbl = self._section(t("file_list"))

        self.auto_remove_var = BooleanVar(
            value=getattr(self.state, "auto_remove_processed", False)
        )
        self._auto_remove_chk = Checkbutton(
            p, text=t("auto_remove"),
            variable=self.auto_remove_var,
            bg=DARK.bg_surface, fg=DARK.text,
            activebackground=DARK.bg_surface, activeforeground=DARK.text,
            selectcolor=DARK.bg_input, bd=0, font=("Segoe UI", 9), anchor="w",
            command=self._on_auto_remove_change,
        )
        self._auto_remove_chk.pack(fill=X, padx=12, pady=2)

        self.auto_save_var = BooleanVar(
            value=getattr(self.state, "auto_save", False)
        )
        self._auto_save_chk = Checkbutton(
            p, text="⚡ Otomatik Kaydet",
            variable=self.auto_save_var,
            bg=DARK.bg_surface, fg=DARK.text,
            activebackground=DARK.bg_surface, activeforeground=DARK.text,
            selectcolor=DARK.bg_input, bd=0, font=("Segoe UI", 9), anchor="w",
            command=self._on_auto_save_change,
        )
        self._auto_save_chk.pack(fill=X, padx=12, pady=2)

        # ── Cache ────────────────────────────────
        Frame(p, bg=DARK.border, height=1).pack(fill=X, padx=12, pady=8)
        self._cache_section_lbl = self._section(t("cache"))
        self._clear_cache_btn = Button(
            p, text=t("clear_cache"),
            command=self.controller.clear_cache,
            bg=DARK.bg_raised, fg=DARK.text, relief="flat", bd=0,
            cursor="hand2", font=("Segoe UI", 9), pady=6,
        )
        self._clear_cache_btn.pack(fill=X, padx=12, pady=4)

        # ── About ────────────────────────────────
        from utils.constants import APP_NAME, APP_VERSION
        Frame(p, bg=DARK.border, height=1).pack(fill=X, padx=12, pady=8)
        self._about_section_lbl = self._section(t("about"))
        self._about_card = Frame(p, bg=self._palette.bg_raised)
        self._about_card.pack(fill=X, padx=12, pady=4)
        Label(self._about_card, text=APP_NAME, bg=self._palette.bg_raised, fg=self._palette.text,
              font=("Segoe UI", 11, "bold"), anchor="w"
              ).pack(fill=X, padx=12, pady=(10, 2))
        Label(self._about_card, text=f"v{APP_VERSION}", bg=self._palette.bg_raised,
              fg=self._palette.text_muted, font=("Segoe UI", 9), anchor="w"
              ).pack(fill=X, padx=12)
        Label(self._about_card, text="Created by Riindewin", bg=self._palette.bg_raised,
              fg=self._palette.text_muted, font=("Segoe UI", 9, "italic"), anchor="w"
              ).pack(fill=X, padx=12, pady=(2, 0))
        self._about_desc = Label(
            self._about_card,
            text="Hafif, hızlı, offline görsel işleme aracı." if get_language() == "tr"
                 else "Lightweight, fast, offline image processing tool.",
            bg=self._palette.bg_raised, fg=self._palette.text_muted, font=("Segoe UI", 8),
            anchor="w", justify="left", wraplength=260,
        )
        self._about_desc.pack(fill=X, padx=12, pady=(4, 12))

        Frame(p, bg=DARK.bg_surface, height=16).pack()

    # ── Language ─────────────────────────────────

    def _on_lang_selected(self, _=None) -> None:
        lang = self._lang_var.get()
        set_language(lang)

    def _on_lang_change(self, lang: str) -> None:
        """Called by i18n when language changes — update all labels."""
        self.apply_language()
        # Notify controller to update topbar + tab labels
        try:
            self.controller.apply_language(lang)
        except Exception:
            pass

    def apply_language(self) -> None:
        """Refresh all text labels in this tab."""
        try:
            self._lang_combo.configure(values=["tr", "en"])
            self._lang_var.set(get_language())
        except Exception:
            pass
        try:
            self.log_toggle_btn.configure(
                text=t("hide_log") if self._log_visible else t("show_log")
            )
        except Exception:
            pass
        try:
            self._auto_remove_chk.configure(text=t("auto_remove"))
        except Exception:
            pass
        try:
            self._clear_cache_btn.configure(text=t("clear_cache"))
        except Exception:
            pass
        try:
            lang = get_language()
            self._about_desc.configure(
                text="Hafif, hızlı, offline görsel işleme aracı." if lang == "tr"
                     else "Lightweight, fast, offline image processing tool."
            )
        except Exception:
            pass
        # Update section labels
        _section_map = {
            "_lang_section_lbl": "language",
            "_theme_section_lbl": "theme",
            "_log_section_lbl": "activity_log",
            "_filelist_section_lbl": "file_list",
            "_cache_section_lbl": "cache",
            "_about_section_lbl": "about",
        }
        for attr, key in _section_map.items():
            lbl = getattr(self, attr, None)
            if lbl:
                try:
                    lbl.configure(text=t(key).upper())
                except Exception:
                    pass

    # ── Log ──────────────────────────────────────

    def _toggle_log(self):
        self._log_visible = not self._log_visible
        if self._log_visible:
            self._log_panel.pack(fill=X, padx=12, pady=(0, 8))
            self.log_toggle_btn.configure(text=t("hide_log"))
        else:
            self._log_panel.pack_forget()
            self.log_toggle_btn.configure(text=t("show_log"))

    def append_log(self, message: str) -> None:
        self._log_messages.append(message)
        self._log_text.configure(state="normal")
        self._log_text.insert(END, message + "\n")
        self._log_text.see(END)
        self._log_text.configure(state="disabled")

    # ── Theme cards ──────────────────────────────

    def _make_theme_card(self, master, palette: ThemePalette) -> Frame:
        card = Frame(master, bg=palette.bg_surface, cursor="hand2")

        swatch_row = Frame(card, bg=palette.bg_surface)
        swatch_row.pack(side=LEFT, padx=8, pady=6)
        for color in (palette.bg_base, palette.bg_surface, palette.accent):
            Frame(swatch_row, bg=color, width=14, height=14).pack(side=LEFT, padx=1)

        Label(card, text=palette.display_name, bg=palette.bg_surface,
              fg=palette.text, font=("Segoe UI", 9, "bold"), anchor="w"
              ).pack(side=LEFT, padx=4)

        card.bind("<Button-1>", lambda e, n=palette.name: self._select_theme(n))
        for child in card.winfo_children():
            child.bind("<Button-1>", lambda e, n=palette.name: self._select_theme(n))
        for child in swatch_row.winfo_children():
            child.bind("<Button-1>", lambda e, n=palette.name: self._select_theme(n))

        return card

    def _select_theme(self, theme_name: str) -> None:
        self.controller.apply_theme_by_name(theme_name)
        self._highlight_active_theme()

    def _highlight_active_theme(self) -> None:
        current = getattr(self.controller, "_theme_name", "dark")
        for name, card in self._theme_btns.items():
            palette = ALL_THEMES[name]
            outline = palette.accent if name == current else palette.border
            card.configure(highlightthickness=2, highlightbackground=outline)

    # ── Callbacks ────────────────────────────────

    def _on_auto_remove_change(self):
        self.state.auto_remove_processed = self.auto_remove_var.get()

    def _on_auto_save_change(self):
        self.state.auto_save = self.auto_save_var.get()

    # ── Section label ────────────────────────────

    def _section(self, text: str) -> Label:
        palette = getattr(self, "_palette", DARK)
        lbl = Label(self.inner, text=text.upper(), bg=palette.bg_surface, fg=palette.text_muted,
                    font=("Segoe UI", 7, "bold"), anchor="w")
        lbl.pack(fill=X, padx=12, pady=(12, 3))
        return lbl

    # ── Theme ────────────────────────────────────

    # Overload for (panel_bg, element_bg, border_color, text_color) signature
    def apply_theme(self, *args) -> None:  # type: ignore[override]
        if len(args) == 1 and isinstance(args[0], ThemePalette):
            palette = args[0]
        elif len(args) == 4:
            # Called as apply_theme(panel_bg, element_bg, border_color, text_color)
            from utils.themes import ALL_THEMES, DEFAULT_THEME
            palette = getattr(self, "_palette", ALL_THEMES[DEFAULT_THEME])
            # Just update bg/fg manually
            panel_bg, element_bg, border_color, text_color = args
            self.configure(bg=panel_bg)
            if hasattr(self, "inner"):
                self.inner.configure(bg=panel_bg)
            if hasattr(self, "_canvas"):
                self._canvas.configure(bg=panel_bg)
            if hasattr(self, "_log_text"):
                self._log_text.configure(bg=element_bg)
            if hasattr(self, "_log_panel"):
                self._log_panel.configure(bg=element_bg)
            if hasattr(self, "log_toggle_btn"):
                self.log_toggle_btn.configure(bg=element_bg, fg=text_color)
            if hasattr(self, "_clear_cache_btn"):
                self._clear_cache_btn.configure(bg=element_bg, fg=text_color)
            if hasattr(self, "_lang_hint"):
                self._lang_hint.configure(bg=panel_bg, fg=text_color)
            for attr in ("_lang_section_lbl", "_theme_section_lbl", "_log_section_lbl",
                         "_filelist_section_lbl", "_cache_section_lbl", "_about_section_lbl"):
                lbl = getattr(self, attr, None)
                if lbl:
                    try:
                        lbl.configure(bg=panel_bg, fg=text_color)
                    except Exception:
                        pass
            if hasattr(self, "_auto_remove_chk"):
                self._auto_remove_chk.configure(
                    bg=panel_bg, fg=text_color,
                    activebackground=panel_bg, activeforeground=text_color,
                    selectcolor=element_bg,
                )
            if hasattr(self, "_auto_save_chk"):
                self._auto_save_chk.configure(
                    bg=panel_bg, fg=text_color,
                    activebackground=panel_bg, activeforeground=text_color,
                    selectcolor=element_bg,
                )
            self._highlight_active_theme()
            if hasattr(self, "_about_card"):
                self._about_card.configure(bg=element_bg)
                for child in self._about_card.winfo_children():
                    try:
                        child.configure(bg=element_bg, fg=text_color)
                    except Exception:
                        pass
            return
        else:
            return
        # ThemePalette path
        self._palette = palette
        self.configure(bg=palette.bg_surface)
        if hasattr(self, "inner"):
            self.inner.configure(bg=palette.bg_surface)
        if hasattr(self, "_canvas"):
            self._canvas.configure(bg=palette.bg_surface)
        if hasattr(self, "_log_text"):
            self._log_text.configure(bg=palette.bg_input, fg=palette.log_fg)
        if hasattr(self, "_log_panel"):
            self._log_panel.configure(bg=palette.bg_input)
        if hasattr(self, "log_toggle_btn"):
            self.log_toggle_btn.configure(bg=palette.bg_raised, fg=palette.text,
                                          activebackground=palette.bg_hover)
        if hasattr(self, "_clear_cache_btn"):
            self._clear_cache_btn.configure(bg=palette.bg_raised, fg=palette.text,
                                            activebackground=palette.bg_hover)
        if hasattr(self, "_lang_hint"):
            self._lang_hint.configure(bg=palette.bg_surface, fg=palette.text_muted)
        for attr in ("_lang_section_lbl", "_theme_section_lbl", "_log_section_lbl",
                     "_filelist_section_lbl", "_cache_section_lbl", "_about_section_lbl"):
            lbl = getattr(self, attr, None)
            if lbl:
                try:
                    lbl.configure(bg=palette.bg_surface, fg=palette.text_muted)
                except Exception:
                    pass
        if hasattr(self, "_auto_remove_chk"):
            self._auto_remove_chk.configure(
                bg=palette.bg_surface, fg=palette.text,
                activebackground=palette.bg_surface, activeforeground=palette.text,
                selectcolor=palette.bg_input,
            )
        self._highlight_active_theme()
        if hasattr(self, "_about_card"):
            self._about_card.configure(bg=palette.bg_raised)
            for child in self._about_card.winfo_children():
                try:
                    child.configure(bg=palette.bg_raised, fg=palette.text_muted)
                except Exception:
                    pass
