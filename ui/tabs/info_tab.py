"""
InfoTab — dosya bilgisi ve EXIF metadata görüntüleyici.
"""

from tkinter import Frame, Label, Canvas, Scrollbar, X, Y, LEFT, RIGHT, BOTH
from utils.constants import C_BG_SURFACE, C_BG_RAISED, C_BG_INPUT, C_BORDER, C_TEXT, C_TEXT_MUTED
from utils.i18n import t


class InfoTab(Frame):

    def __init__(self, master, controller, state):
        super().__init__(master, bg=C_BG_SURFACE)
        self.controller = controller
        self.state = state
        self._build()

    def _build(self):
        sb = Scrollbar(self, orient="vertical", width=6)
        sb.pack(side=RIGHT, fill=Y)
        self._canvas = Canvas(self, bg=C_BG_SURFACE, highlightthickness=0,
                              yscrollcommand=sb.set)
        self._canvas.pack(side=LEFT, fill=BOTH, expand=True)
        sb.config(command=self._canvas.yview)

        self.inner = Frame(self._canvas, bg=C_BG_SURFACE)
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

        # Placeholder
        self._placeholder = Label(
            self.inner,
            text="Dosya seçin",
            bg=C_BG_SURFACE, fg=C_TEXT_MUTED,
            font=("Segoe UI", 9), anchor="w",
        )
        self._placeholder.pack(fill=X, padx=14, pady=14)

    def update(self, path: str) -> None:
        """Dosya seçildiğinde EXIF ve temel bilgileri güncelle."""
        # Mevcut widget'ları temizle
        for child in self.inner.winfo_children():
            child.destroy()

        try:
            from core.exif_reader import ExifReader
            basic = ExifReader.get_basic_info(path)
            exif = ExifReader.read(path)
        except Exception:
            basic = {}
            exif = {}

        # Temel bilgiler bölümü
        self._section("Dosya Bilgisi")
        for key, val in basic.items():
            self._row(key, str(val))

        # EXIF bölümü
        if exif:
            self._section("EXIF / Metadata")
            for key, val in exif.items():
                self._row(key, str(val))
        else:
            Label(
                self.inner,
                text="EXIF verisi bulunamadı",
                bg=C_BG_SURFACE, fg=C_TEXT_MUTED,
                font=("Segoe UI", 8), anchor="w",
            ).pack(fill=X, padx=14, pady=4)

        Frame(self.inner, bg=C_BG_SURFACE, height=16).pack()

    def _section(self, text: str) -> None:
        Label(
            self.inner,
            text=text.upper(),
            bg=C_BG_SURFACE, fg=C_TEXT_MUTED,
            font=("Segoe UI", 7, "bold"), anchor="w",
        ).pack(fill=X, padx=12, pady=(12, 3))

    def _row(self, key: str, value: str) -> None:
        row = Frame(self.inner, bg=C_BG_RAISED)
        row.pack(fill=X, padx=12, pady=1)
        Label(row, text=key, bg=C_BG_RAISED, fg=C_TEXT_MUTED,
              font=("Segoe UI", 8), width=16, anchor="w",
              ).pack(side=LEFT, padx=(8, 4), pady=4)
        Label(row, text=value, bg=C_BG_RAISED, fg=C_TEXT,
              font=("Segoe UI", 8), anchor="w", wraplength=180,
              ).pack(side=LEFT, fill=X, expand=True, padx=(0, 8), pady=4)

    def apply_language(self) -> None:
        pass

    def apply_theme(self, panel_bg, element_bg, border_color, text_color):
        self.configure(bg=panel_bg)
        try:
            self.inner.configure(bg=panel_bg)
            self._canvas.configure(bg=panel_bg)
        except Exception:
            pass
