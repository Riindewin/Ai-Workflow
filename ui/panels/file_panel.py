"""
FilePanel — left sidebar with checkbox list and status icons.

Each row: [checkbox] [status_icon] [filename]
Status icons: ⬜ pending, ⏳ processing, ✓ done, ❌ error
"""

import os
from tkinter import (
    Frame, Label, Button, Canvas, Scrollbar,
    X, Y, LEFT, RIGHT, BOTH, BOTTOM, END
)
from utils.themes import ThemePalette, DARK
from utils.constants import SIDEBAR_WIDTH

STATUS_ICONS = {
    "pending":    "⬜",
    "processing": "⏳",
    "done":       "✓ ",
    "error":      "❌",
}


class FilePanel:

    def __init__(self, master, controller):
        self.controller = controller
        self._palette = DARK

        self.frame = Frame(master, bg=DARK.bg_surface, width=SIDEBAR_WIDTH)
        self.frame.pack(side=LEFT, fill=Y)
        self.frame.pack_propagate(False)

        # ── Header ──────────────────────────────
        self._header_frame = Frame(self.frame, bg=DARK.bg_surface, height=44)
        self._header_frame.pack(fill=X)
        self._header_frame.pack_propagate(False)

        self._header_title_lbl = Label(self._header_frame, text="DOSYALAR", bg=DARK.bg_surface, fg=DARK.text_muted,
              font=("Segoe UI", 9, "bold"), anchor="w").pack(side=LEFT, padx=14)

        self._count_label = Label(self._header_frame, text="0", bg=DARK.bg_raised,
                                  fg=DARK.text_muted, font=("Segoe UI", 8),
                                  padx=6, pady=1)
        self._count_label.pack(side=RIGHT, padx=10)

        Frame(self.frame, bg=DARK.border, height=1).pack(fill=X)

        # ── File list (custom canvas-based) ─────
        self._list_container = Frame(self.frame, bg=DARK.bg_surface)
        self._list_container.pack(fill=BOTH, expand=True, padx=4, pady=4)

        self._sb = Scrollbar(self._list_container, orient="vertical", width=6)
        self._sb.pack(side=RIGHT, fill=Y)

        self._canvas = Canvas(self._list_container, bg=DARK.bg_input,
                              highlightthickness=0,
                              yscrollcommand=self._sb.set)
        self._canvas.pack(side=LEFT, fill=BOTH, expand=True)
        self._sb.config(command=self._canvas.yview)

        self._list_frame = Frame(self._canvas, bg=DARK.bg_input)
        self._list_win = self._canvas.create_window(
            (0, 0), window=self._list_frame, anchor="nw"
        )
        self._list_frame.bind("<Configure>", self._on_list_configure)
        self._canvas.bind("<Configure>", self._on_canvas_resize)
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self._canvas.bind(seq, self._on_scroll)
            self._list_frame.bind(seq, self._on_scroll)
        # ── State ───────────────────────────────
        self._files: list[str] = []
        self._checked: set[str] = set()
        self._status: dict[str, str] = {}   # path → status key
        self._row_widgets: list[dict] = []
        self._selected_idx: int = -1
        self._thumbnails: dict[str, "ImageTk.PhotoImage"] = {}

        # ── Bottom buttons ───────────────────────
        Frame(self.frame, bg=DARK.border, height=1).pack(fill=X)

        btn_bar = Frame(self.frame, bg=DARK.bg_surface, height=48)
        btn_bar.pack(fill=X)
        btn_bar.pack_propagate(False)

        self.add_btn = self._make_btn(btn_bar, "＋  Ekle",
                                      controller.select_files, accent=True)
        self.add_btn.pack(side=LEFT, fill=BOTH, expand=True, padx=(8, 4), pady=8)

        self.remove_btn = self._make_btn(btn_bar, "✕  Sil",
                                         controller.remove_selected)
        self.remove_btn.pack(side=LEFT, fill=BOTH, expand=True, padx=(4, 8), pady=8)

    # ════════════════════════════════════════════
    #  Public API
    # ════════════════════════════════════════════

    def update_list(self, files: list[str]) -> None:
        """Rebuild the file list rows."""
        self._files = list(files)
        # Artık listede olmayan dosyaların thumbnail'larını temizle
        for path in list(self._thumbnails.keys()):
            if path not in files:
                del self._thumbnails[path]
        # Preserve checked/status for existing paths
        for path in list(self._checked):
            if path not in files:
                self._checked.discard(path)
        for path in list(self._status):
            if path not in files:
                del self._status[path]

        self._rebuild_rows()
        self._count_label.configure(text=str(len(files)))

    def set_status(self, path: str, status: str) -> None:
        """Update status icon for a file. status: pending/processing/done/error"""
        self._status[path] = status
        self._update_row_status(path)

    def get_checked_files(self) -> list[str]:
        return [f for f in self._files if f in self._checked]

    def select_all(self) -> None:
        self._checked = set(self._files)
        self._rebuild_rows()

    def deselect_all(self) -> None:
        self._checked.clear()
        self._rebuild_rows()

    def get_selected_index(self) -> int:
        return self._selected_idx

    # Compatibility shim for old code using listbox.curselection()
    @property
    def listbox(self):
        return _ListboxShim(self)

    # ════════════════════════════════════════════
    #  Row building
    # ════════════════════════════════════════════

    def _rebuild_rows(self) -> None:
        for w in self._list_frame.winfo_children():
            w.destroy()
        self._row_widgets.clear()

        for idx, path in enumerate(self._files):
            self._build_row(idx, path)

        self._list_frame.update_idletasks()
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _build_row(self, idx: int, path: str) -> None:
        p = self._palette
        is_checked = path in self._checked
        is_selected = (idx == self._selected_idx)

        row_bg = p.bg_hover if is_selected else p.bg_input

        row = Frame(self._list_frame, bg=row_bg, cursor="hand2")
        row.pack(fill=X, pady=1)

        # Checkbox
        chk_text = "☑" if is_checked else "☐"
        chk = Label(row, text=chk_text, bg=row_bg, fg=p.accent if is_checked else p.text_muted,
                    font=("Segoe UI", 10), cursor="hand2", padx=4)

        # Thumbnail
        thumb_img = self._thumbnails.get(path)
        if thumb_img:
            from PIL import ImageTk as _ImageTk
            thumb_lbl = Label(row, image=thumb_img, bg=row_bg, cursor="hand2")
            thumb_lbl.image = thumb_img  # GC koruması
            thumb_lbl.pack(side=LEFT, padx=(4, 0))
            thumb_lbl.bind("<Button-1>", lambda e, i=idx: self._select_row(i))
            for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                thumb_lbl.bind(seq, self._on_scroll)
        else:
            # Placeholder (48x48 boş alan)
            ph = Frame(row, bg=row_bg, width=48, height=48)
            ph.pack(side=LEFT, padx=(4, 0))
            ph.pack_propagate(False)
            # Async yükle
            self._load_thumbnail_async(path)

        chk.pack(side=LEFT)
        chk.bind("<Button-1>", lambda e, p=path: self._toggle_check(p))

        # Status icon
        status = self._status.get(path, "pending")
        icon_text = STATUS_ICONS.get(status, "⬜")
        icon_color = {
            "done": p.accent, "error": "#e05555",
            "processing": p.text_muted, "pending": p.text_muted,
        }.get(status, p.text_muted)

        status_lbl = Label(row, text=icon_text, bg=row_bg, fg=icon_color,
                           font=("Segoe UI", 9), width=2)
        status_lbl.pack(side=LEFT)

        # Filename
        name = os.path.basename(path)
        name_lbl = Label(row, text=f"  {name}", bg=row_bg, fg=p.text,
                         font=("Segoe UI", 9), anchor="w", cursor="hand2")
        name_lbl.pack(side=LEFT, fill=X, expand=True)

        # Click to select
        for widget in (row, name_lbl, status_lbl):
            widget.bind("<Button-1>", lambda e, i=idx: self._select_row(i))

        # Scroll bindings
        for widget in (row, chk, status_lbl, name_lbl):
            for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                widget.bind(seq, self._on_scroll)

        # Sağ tık context menüsü
        for widget in (row, chk, status_lbl, name_lbl):
            widget.bind("<Button-3>", lambda e, p=path: self._show_context_menu(p, e))

        self._row_widgets.append({
            "row": row, "chk": chk, "status": status_lbl,
            "name": name_lbl, "path": path,
        })

    def _select_row(self, idx: int) -> None:
        self._selected_idx = idx
        self._rebuild_rows()
        if 0 <= idx < len(self._files):
            self.controller.on_file_selected(idx)

    def _toggle_check(self, path: str) -> None:
        if path in self._checked:
            self._checked.discard(path)
        else:
            self._checked.add(path)
        self._rebuild_rows()

    def _update_row_status(self, path: str) -> None:
        for w in self._row_widgets:
            if w["path"] == path:
                status = self._status.get(path, "pending")
                icon_text = STATUS_ICONS.get(status, "⬜")
                icon_color = {
                    "done": self._palette.accent, "error": "#e05555",
                    "processing": self._palette.text_muted,
                    "pending": self._palette.text_muted,
                }.get(status, self._palette.text_muted)
                try:
                    w["status"].configure(text=icon_text, fg=icon_color)
                except Exception:
                    pass
                break

    def _show_context_menu(self, path: str, event) -> None:
        """Sağ tık context menüsü göster."""
        import tkinter as tk
        menu = tk.Menu(self._canvas, tearoff=0)
        menu.add_command(label="✨ Dönüştür",
                         command=lambda: self.controller.start_convert())
        menu.add_command(label="🚀 AI Upscale",
                         command=lambda: self.controller.upscale_selected())
        menu.add_command(label="🪄 Arka Plan Kaldır",
                         command=lambda: self.controller.remove_background_selected())
        menu.add_separator()
        menu.add_command(label="🗑 Sil",
                         command=lambda: self._remove_file(path))
        menu.add_command(label="📂 Dosya Konumunu Aç",
                         command=lambda: self._open_file_location(path))
        try:
            menu.post(event.x_root, event.y_root)
        except Exception:
            pass

    def _remove_file(self, path: str) -> None:
        """Dosyayı listeden sil."""
        try:
            idx = self._files.index(path)
            self._files.pop(idx)
            self.controller.state.files.pop(idx)
            self._thumbnails.pop(path, None)
            self._rebuild_rows()
            self._count_label.configure(text=str(len(self._files)))
        except Exception:
            pass

    def _open_file_location(self, path: str) -> None:
        """Dosyanın bulunduğu klasörü Windows Explorer'da aç."""
        import os
        try:
            folder = os.path.dirname(path)
            os.startfile(folder)
        except Exception:
            pass

    def _load_thumbnail_async(self, path: str) -> None:
        """Arka planda thumbnail oluştur."""
        if path in self._thumbnails:
            return
        import threading
        threading.Thread(target=self._make_thumbnail, args=(path,), daemon=True).start()

    def _make_thumbnail(self, path: str) -> None:
        """Thread'de PIL thumbnail oluştur."""
        try:
            from PIL import Image, ImageTk
            with Image.open(path) as img:
                img.load()
                thumb = img.copy()
            thumb.thumbnail((48, 48), Image.LANCZOS)
            # RGBA → RGB (JPEG uyumluluğu için)
            if thumb.mode == "RGBA":
                bg = Image.new("RGB", thumb.size, (30, 30, 30))
                bg.paste(thumb, mask=thumb.split()[3])
                thumb = bg
            elif thumb.mode != "RGB":
                thumb = thumb.convert("RGB")
            photo = ImageTk.PhotoImage(thumb)
            self._thumbnails[path] = photo
            # Ana thread'de satırı güncelle
            try:
                self.controller.root.after(0, lambda p=path: self._refresh_row(p))
            except Exception:
                pass
        except Exception:
            pass

    def _refresh_row(self, path: str) -> None:
        """Belirli bir dosyanın satırını yeniden oluştur."""
        try:
            idx = self._files.index(path)
            # Sadece o satırı yeniden oluştur
            for w in self._row_widgets:
                if w["path"] == path:
                    w["row"].destroy()
                    self._row_widgets.remove(w)
                    break
            self._build_row(idx, path)
            self._list_frame.update_idletasks()
            self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        except Exception:
            pass

    # ════════════════════════════════════════════
    #  Scroll helpers
    # ════════════════════════════════════════════

    def _on_list_configure(self, _=None):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_resize(self, event):
        self._canvas.itemconfig(self._list_win, width=event.width)

    def _on_scroll(self, event):
        if event.num == 5 or event.delta < 0:
            self._canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            self._canvas.yview_scroll(-1, "units")

    # ════════════════════════════════════════════
    #  Widget factory
    # ════════════════════════════════════════════

    def _make_btn(self, master, text, command, accent=False):
        p = self._palette
        bg = p.accent if accent else p.bg_raised
        fg = p.btn_fg if accent else p.text
        return Button(master, text=text, command=command,
                      bg=bg, fg=fg, activebackground=p.bg_hover,
                      activeforeground=fg, relief="flat", bd=0,
                      font=("Segoe UI", 9, "bold"), cursor="hand2")

    # ════════════════════════════════════════════
    #  Theme
    # ════════════════════════════════════════════

    def apply_theme(self, palette: ThemePalette) -> None:
        self._palette = palette
        self.frame.configure(bg=palette.bg_surface)
        self._canvas.configure(bg=palette.bg_input)
        self._list_frame.configure(bg=palette.bg_input)
        self._count_label.configure(bg=palette.bg_raised, fg=palette.text_muted)
        self.add_btn.configure(bg=palette.accent, fg=palette.btn_fg,
                               activebackground=palette.accent_dim)
        self.remove_btn.configure(bg=palette.bg_raised, fg=palette.text,
                                  activebackground=palette.bg_hover)
        # Header frame ve title label
        try:
            self._header_frame.configure(bg=palette.bg_surface)
        except Exception:
            pass
        for child in self._header_frame.winfo_children():
            try:
                cls = child.winfo_class()
                if cls == "Label":
                    child.configure(bg=palette.bg_surface, fg=palette.text_muted)
            except Exception:
                pass
        # List container
        try:
            self._list_container.configure(bg=palette.bg_surface)
        except Exception:
            pass
        # Scrollbar
        try:
            self._sb.configure(bg=palette.bg_surface)
        except Exception:
            pass
        self._rebuild_rows()


class _ListboxShim:
    """Compatibility shim so old code using file_panel.listbox.curselection() still works."""
    def __init__(self, panel: FilePanel):
        self._panel = panel

    def curselection(self):
        idx = self._panel._selected_idx
        return (idx,) if idx >= 0 else ()

    def drop_target_register(self, *args):
        try:
            self._panel._canvas.drop_target_register(*args)
        except Exception:
            pass

    def dnd_bind(self, event, callback):
        try:
            self._panel._canvas.dnd_bind(event, callback)
        except Exception:
            pass
