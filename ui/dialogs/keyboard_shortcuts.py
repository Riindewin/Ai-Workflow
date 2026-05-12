"""
KeyboardShortcutsWindow — opened with ? key.
"""

from tkinter import Toplevel, Frame, Label, Button, X, LEFT, BOTH, Y, Scrollbar

SHORTCUTS = [
    ("Ctrl + Z",     "Geri Al (Undo)"),
    ("Ctrl + Y",     "Yinele (Redo)"),
    ("Ctrl + S",     "Kaydet"),
    ("Ctrl + O",     "Dosya Aç"),
    ("?",            "Bu pencereyi aç"),
    ("Delete",       "Seçili dosyayı sil"),
    ("Ctrl + A",     "Tümünü seç"),
    ("Escape",       "Kırpma modunu iptal et"),
    ("Space",        "Dönüştür"),
    ("U",            "AI Upscale"),
    ("R",            "90° Döndür"),
    ("F",            "Yatay Çevir"),
    ("C",            "Kırpma Modu"),
    ("B",            "Arka Plan Kaldır"),
    ("Scroll",       "Önizlemede zoom"),
    ("Sol tık sürükle", "Önizlemede pan (kaydır)"),
]


class KeyboardShortcutsWindow(Toplevel):

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Klavye Kısayolları")
        self.resizable(False, False)
        self.configure(bg="#161616")
        self.bind("<Escape>", lambda _: self.destroy())

        Label(self, text="Klavye Kısayolları", bg="#161616", fg="#e8e8e8",
              font=("Segoe UI", 13, "bold")).pack(padx=20, pady=(16, 8))

        Frame(self, bg="#2d2d2d", height=1).pack(fill=X, padx=16)

        for key, desc in SHORTCUTS:
            row = Frame(self, bg="#161616")
            row.pack(fill=X, padx=20, pady=3)
            Label(row, text=key, bg="#252525", fg="#00c896",
                  font=("Consolas", 9, "bold"), padx=8, pady=3,
                  width=22, anchor="w").pack(side=LEFT)
            Label(row, text=desc, bg="#161616", fg="#e8e8e8",
                  font=("Segoe UI", 9), padx=8).pack(side=LEFT)

        Frame(self, bg="#2d2d2d", height=1).pack(fill=X, padx=16, pady=(8, 0))

        Button(self, text="Kapat", command=self.destroy,
               bg="#252525", fg="#e8e8e8", relief="flat", bd=0,
               cursor="hand2", font=("Segoe UI", 9), pady=6
               ).pack(fill=X, padx=20, pady=12)

        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        px = parent.winfo_rootx() + (parent.winfo_width()  - w) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self.geometry(f"+{px}+{py}")
        self.grab_set()
