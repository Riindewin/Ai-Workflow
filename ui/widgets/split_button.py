"""
SplitButton — Bileşik buton widget'ı.

Layout:
  [ Ana Eylem Butonu ][ ▼ ]

Sol buton ana eylemi tetikler.
Sağ buton (▼) tıklandığında tk.Menu popup gösterir.
"""

import tkinter as tk
from tkinter import Frame, Button

from utils.constants import C_TEXT


class SplitButton(Frame):
    """
    İki parçalı bileşik buton.

    Parameters
    ----------
    master      : üst widget
    main_text   : sol butonun başlangıç etiketi
    main_command: sol butona tıklandığında çağrılacak callable
    menu_items  : [(etiket, callable), ...] — sağ menü öğeleri
    bg          : normal arka plan rengi
    hover       : hover arka plan rengi
    **kwargs    : Frame'e iletilir
    """

    def __init__(
        self,
        master,
        main_text: str,
        main_command,
        menu_items: list[tuple[str, callable]],
        bg: str,
        hover: str,
        **kwargs,
    ):
        # Frame'e iletilmemesi gereken özel parametreleri ayır
        super().__init__(master, bg=bg, **kwargs)

        self._bg = bg
        self._hover = hover
        self._menu_items = menu_items

        # ── Sol buton (ana eylem) ─────────────────
        self._main_btn = Button(
            self,
            text=main_text,
            command=main_command,
            bg=bg,
            fg=C_TEXT,
            activebackground=hover,
            activeforeground=C_TEXT,
            relief="flat",
            bd=0,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
            padx=14,
        )
        self._main_btn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ── Ayırıcı çizgi ────────────────────────
        self._sep = Frame(self, bg=self._darken(bg), width=1)
        self._sep.pack(side=tk.LEFT, fill=tk.Y, pady=4)

        # ── Sağ buton (▼ açılır menü) ─────────────
        self._arrow_btn = Button(
            self,
            text="▼",
            command=self._show_menu,
            bg=bg,
            fg=C_TEXT,
            activebackground=hover,
            activeforeground=C_TEXT,
            relief="flat",
            bd=0,
            font=("Segoe UI", 8),
            cursor="hand2",
            padx=8,
        )
        self._arrow_btn.pack(side=tk.LEFT, fill=tk.BOTH)

        # ── Hover efektleri ───────────────────────
        for btn in (self._main_btn, self._arrow_btn):
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=self._hover))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=self._bg))

    def apply_theme(self, bg: str, hover: str, text_color: str) -> None:
        """Tema renklerini günceller."""
        self._bg = bg
        self._hover = hover
        self.configure(bg=bg)
        self._main_btn.configure(bg=bg, fg=text_color,
                                 activebackground=hover, activeforeground=text_color)
        self._arrow_btn.configure(bg=bg, fg=text_color,
                                  activebackground=hover, activeforeground=text_color)
        self._sep.configure(bg=self._darken(bg))
        # Hover binding'leri yeni renklerle güncelle
        for btn in (self._main_btn, self._arrow_btn):
            btn.unbind("<Enter>")
            btn.unbind("<Leave>")
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=self._hover))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=self._bg))

    # ── Public API ────────────────────────────────

    def update_label(self, text: str) -> None:
        """Sol buton etiketini günceller."""
        self._main_btn.configure(text=text)

    def set_enabled(self, enabled: bool) -> None:
        """Her iki butonu etkinleştirir veya devre dışı bırakır."""
        state = tk.NORMAL if enabled else tk.DISABLED
        self._main_btn.configure(state=state)
        self._arrow_btn.configure(state=state)

    # ── Private ───────────────────────────────────

    def _show_menu(self, event=None) -> None:
        """Sağ butona tıklandığında popup menüyü oluşturur ve gösterir."""
        menu = tk.Menu(self, tearoff=0)

        for label, command in self._menu_items:
            menu.add_command(label=label, command=command)

        # Menüyü sağ butonun hemen altında göster
        x = self._arrow_btn.winfo_rootx()
        y = self._arrow_btn.winfo_rooty() + self._arrow_btn.winfo_height()
        menu.post(x, y)

    @staticmethod
    def _darken(hex_color: str) -> str:
        """Verilen hex rengi biraz koyulaştırır (ayırıcı çizgi için)."""
        try:
            hex_color = hex_color.lstrip("#")
            r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            r = max(0, r - 30)
            g = max(0, g - 30)
            b = max(0, b - 30)
            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, AttributeError):
            return "#000000"
