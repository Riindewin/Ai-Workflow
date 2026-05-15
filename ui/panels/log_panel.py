"""
LogPanel — compact activity log inside the right sidebar.

Fixed height so it never pushes the action bar off screen.
"""

from tkinter import Frame, Label, Text, Scrollbar, X, BOTH, RIGHT, LEFT, Y, END
from utils.constants import (
    C_BG_SURFACE, C_BG_INPUT, C_BORDER, C_TEXT_MUTED, C_LOG_FG,
    L_BG_SURFACE, L_BG_INPUT, L_LOG_FG,
)

LOG_PANEL_HEIGHT = 180   # fixed pixel height


class LogPanel:

    def __init__(self, master):
        self.frame = Frame(
            master,
            bg=C_BG_SURFACE,
            height=LOG_PANEL_HEIGHT,
        )
        self.frame.pack_propagate(False)

        # ── Header ──────────────────────────────
        header = Frame(self.frame, bg=C_BG_SURFACE, height=32)
        header.pack(fill=X)
        header.pack_propagate(False)

        Label(
            header,
            text="AKTİVİTE",
            bg=C_BG_SURFACE,
            fg=C_TEXT_MUTED,
            font=("Segoe UI", 7, "bold"),
            anchor="w",
        ).pack(side=LEFT, padx=14)

        Frame(self.frame, bg=C_BORDER, height=1).pack(fill=X)

        # ── Text area ───────────────────────────
        text_frame = Frame(self.frame, bg=C_BG_SURFACE)
        text_frame.pack(fill=BOTH, expand=True, padx=6, pady=6)

        sb = Scrollbar(text_frame, orient="vertical", width=5)
        sb.pack(side=RIGHT, fill=Y)

        self.log_box = Text(
            text_frame,
            bg=C_BG_INPUT,
            fg=C_LOG_FG,
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Consolas", 8),
            wrap="word",
            state="normal",
            yscrollcommand=sb.set,
        )
        self.log_box.pack(side=LEFT, fill=BOTH, expand=True)
        sb.config(command=self.log_box.yview)

    # ── Public API ──────────────────────────────

    def append(self, text: str) -> None:
        self.log_box.insert(END, text + "\n")
        self.log_box.see(END)

    # ── Theme ────────────────────────────────────

    def apply_theme(self, panel_bg, element_bg, border_color, text_color, dark_mode=True):
        self.frame.configure(bg=panel_bg)
        self.log_box.configure(
            bg=element_bg,
            fg=C_LOG_FG if dark_mode else L_LOG_FG,
        )
