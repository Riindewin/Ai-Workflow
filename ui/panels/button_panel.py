"""
ActionBar (simplified) — bottom bar.

Contents: [💾 Kaydet (N)]  [☑ Tümünü Seç]  [☐ Seçimi Kaldır]  ░░ status
"""

from tkinter import Frame, Button, Label, X, LEFT, RIGHT, BOTH, DISABLED, NORMAL
from utils.themes import ThemePalette, DARK
from utils.constants import ACTION_BAR_H


class ButtonPanel:

    def __init__(self, master, controller):
        self.controller = controller
        self._palette = DARK
        self._save_btn_bg = DARK.bg_raised   # track normal bg for hover bindings

        self.frame = Frame(master, bg=DARK.bg_surface, height=ACTION_BAR_H)
        self.frame.pack_propagate(False)

        Frame(self.frame, bg=DARK.border, height=1).pack(fill=X)

        inner = Frame(self.frame, bg=DARK.bg_surface)
        inner.pack(fill=BOTH, expand=True, padx=10, pady=8)

        # ── Save button ──────────────────────────
        self.save_btn = self._make_btn(
            inner, "💾  Kaydet", controller.save_buffer,
            bg=DARK.bg_raised, hover=DARK.bg_hover,
        )
        self.save_btn.configure(state=DISABLED, fg=DARK.text_muted)
        self.save_btn.pack(side=LEFT, padx=(0, 6), fill=BOTH)

        # ── Cancel button (hidden by default) ────
        self._cancel_btn = self._make_btn(
            inner, "⏹ İptal", controller.cancel_batch,
            bg="#e05555", hover="#c0392b",
        )
        self._cancel_btn.configure(fg="white")

        # ── Select all ───────────────────────────
        self.select_all_btn = self._make_btn(
            inner, "☑  Tümünü Seç", controller.select_all_files,
            bg=DARK.bg_raised, hover=DARK.bg_hover,
        )
        self.select_all_btn.pack(side=LEFT, padx=(0, 4), fill=BOTH)

        # ── Deselect all ─────────────────────────
        self.deselect_btn = self._make_btn(
            inner, "☐  Seçimi Kaldır", controller.deselect_all_files,
            bg=DARK.bg_raised, hover=DARK.bg_hover,
        )
        self.deselect_btn.pack(side=LEFT, padx=(0, 12), fill=BOTH)

        # ── Open folder button (hidden by default) ──
        self._open_folder_path: str = ""
        self._open_folder_btn = self._make_btn(
            inner, "📂 Klasörü Aç", self._on_open_folder,
            bg=DARK.bg_raised, hover=DARK.bg_hover,
        )
        # Başlangıçta gizli

        # ── Status / progress ────────────────────
        status_frame = Frame(inner, bg=DARK.bg_surface)
        status_frame.pack(side=LEFT, fill=BOTH, expand=True)

        self.status_label = Label(status_frame, text="Hazır",
                                  bg=DARK.bg_surface, fg=DARK.text_muted,
                                  font=("Segoe UI", 9), anchor="w")
        self.status_label.pack(fill=X)

        self._prog_bg = Frame(status_frame, bg=DARK.bg_raised, height=3)
        self._prog_bg.pack(fill=X, pady=(4, 0))

        self._prog_fill = Frame(self._prog_bg, bg=DARK.accent, height=3, width=0)
        self._prog_fill.place(x=0, y=0, relheight=1.0, relwidth=0.0)

    # ── Helpers ──────────────────────────────────

    def _make_btn(self, master, text, command, bg, hover):
        btn = Button(master, text=text, command=command,
                     bg=bg, fg=DARK.text,
                     activebackground=hover, activeforeground=DARK.text,
                     relief="flat", bd=0, font=("Segoe UI", 9, "bold"),
                     cursor="hand2", padx=12)
        btn.bind("<Enter>", lambda e, b=btn, h=hover:
                 b.configure(bg=h) if str(b["state"]) != "disabled" else None)
        btn.bind("<Leave>", lambda e, b=btn, c=bg:
                 b.configure(bg=c) if str(b["state"]) != "disabled" else None)
        return btn

    # ── Public API ───────────────────────────────

    def set_status(self, text: str) -> None:
        self.status_label.configure(text=text)

    def set_progress(self, fraction: float) -> None:
        fraction = max(0.0, min(1.0, fraction))
        self._prog_fill.place(relwidth=fraction)

    def set_save_count(self, count: int) -> None:
        p = self._palette
        if count <= 0:
            self.save_btn.configure(state=DISABLED, text="💾  Kaydet",
                                    fg=p.text_muted, bg=p.bg_raised)
            self._save_btn_bg = p.bg_raised
        else:
            self.save_btn.configure(state=NORMAL, text=f"💾  Kaydet ({count})",
                                    fg=p.btn_fg, bg="#27ae60")
            self._save_btn_bg = "#27ae60"

    def set_cancel_visible(self, visible: bool) -> None:
        if visible:
            self._cancel_btn.pack(side=LEFT, padx=(0, 6), fill=BOTH)
        else:
            self._cancel_btn.pack_forget()

    def _on_open_folder(self) -> None:
        import os
        try:
            if self._open_folder_path and os.path.isdir(self._open_folder_path):
                os.startfile(self._open_folder_path)
        except Exception:
            pass

    def set_open_folder_visible(self, path) -> None:
        if path:
            self._open_folder_path = path
            self._open_folder_btn.pack(side=LEFT, padx=(0, 6), fill=BOTH)
        else:
            self._open_folder_path = ""
            self._open_folder_btn.pack_forget()

    def set_batch_progress(self, current: int, total: int) -> None:
        self.status_label.configure(text=f"{current}/{total} işleniyor...")
        fraction = current / total if total > 0 else 0.0
        self.set_progress(fraction)

    # ── Theme ────────────────────────────────────

    def apply_theme(self, palette: ThemePalette) -> None:
        self._palette = palette
        self.frame.configure(bg=palette.bg_surface)
        self.status_label.configure(bg=palette.bg_surface, fg=palette.text_muted)
        self._prog_bg.configure(bg=palette.bg_raised)
        self._prog_fill.configure(bg=palette.accent)

        for btn in (self.select_all_btn, self.deselect_btn):
            btn.configure(bg=palette.bg_raised, fg=palette.text,
                          activebackground=palette.bg_hover,
                          activeforeground=palette.text)

        # Kaydet butonu aktif/pasif durumuna göre ayrı renklendirme
        is_active = str(self.save_btn["state"]) != "disabled"
        if is_active:
            self.save_btn.configure(fg=palette.btn_fg,
                                    activebackground=palette.bg_hover,
                                    activeforeground=palette.btn_fg)
        else:
            self.save_btn.configure(bg=palette.bg_raised, fg=palette.text_muted,
                                    activebackground=palette.bg_hover,
                                    activeforeground=palette.text_muted)
            self._save_btn_bg = palette.bg_raised

        self._cancel_btn.configure(bg="#e05555", fg="white",
                                   activebackground="#c0392b",
                                   activeforeground="white")
        self._open_folder_btn.configure(bg=palette.bg_raised, fg=palette.text,
                                        activebackground=palette.bg_hover,
                                        activeforeground=palette.text)
