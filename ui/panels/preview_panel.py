"""
PreviewPanel — center canvas with before/after comparison slider.

Compare mode uses PhotoImage cropping to correctly show left=before, right=after.
"""

from tkinter import Frame, Canvas, Button, Label, BOTH, X, LEFT, RIGHT
from PIL import Image, ImageTk

from utils.constants import (
    C_BG_RAISED, C_BG_INPUT, C_BG_SURFACE,
    C_BORDER, C_TEXT_MUTED, C_TEXT_DIM, C_ACCENT,
)


class PreviewPanel:

    def __init__(self, master):
        self.frame = Frame(master, bg=C_BG_RAISED)
        self.frame.pack(fill=BOTH, expand=True)

        # ── Toolbar ─────────────────────────────
        toolbar = Frame(self.frame, bg=C_BG_RAISED, height=36)
        toolbar.pack(fill=X)
        toolbar.pack_propagate(False)

        Label(
            toolbar,
            text="ÖNİZLEME",
            bg=C_BG_RAISED,
            fg=C_TEXT_MUTED,
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        ).pack(side=LEFT, padx=14)

        btn_frame = Frame(toolbar, bg=C_BG_RAISED)
        btn_frame.pack(side=RIGHT, padx=10)

        self._btn_single  = self._make_toggle(btn_frame, "Tek Görünüm",   self._set_single)
        self._btn_compare = self._make_toggle(btn_frame, "Önce / Sonra",  self._set_compare)
        self._btn_single.pack(side=LEFT, padx=(0, 2))
        self._btn_compare.pack(side=LEFT)

        Frame(self.frame, bg=C_BORDER, height=1).pack(fill=X)

        # ── Canvas ──────────────────────────────
        self.canvas = Canvas(
            self.frame,
            bg=C_BG_INPUT,
            highlightthickness=0,
            cursor="crosshair",
        )
        self.canvas.pack(fill=BOTH, expand=True, padx=12, pady=12)
        self.canvas.bind("<Configure>",       self._on_resize)
        self.canvas.bind("<ButtonPress-1>",   self._on_press)
        self.canvas.bind("<B1-Motion>",       self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        # ── State ───────────────────────────────
        self._mode        = "single"
        self._before_pil  = None   # PIL Image — original
        self._after_pil   = None   # PIL Image — upscaled
        self._before_ref  = None   # kept to prevent GC
        self._after_ref   = None
        self._split_x     = 0.5
        self._dragging    = False

        self._update_toggle_style()
        self._draw_placeholder()

    # ════════════════════════════════════════════
    #  Public API
    # ════════════════════════════════════════════

    def show_image(self, pil_image: Image.Image) -> None:
        """Show a single PIL image."""
        self._before_pil = pil_image
        self._after_pil  = None
        self._mode = "single"
        self._update_toggle_style()
        self._redraw()

    def show_comparison(self, before_pil: Image.Image, after_pil: Image.Image) -> None:
        """Load before/after PIL images and switch to compare mode."""
        self._before_pil = before_pil
        self._after_pil  = after_pil
        self._mode = "compare"
        self._split_x = 0.5
        self._update_toggle_style()
        self._redraw()

    def clear_after(self) -> None:
        self._after_pil = None
        self._mode = "single"
        self._update_toggle_style()
        self._redraw()

    # ════════════════════════════════════════════
    #  Mode toggles
    # ════════════════════════════════════════════

    def _set_single(self):
        self._mode = "single"
        self._update_toggle_style()
        self._redraw()

    def _set_compare(self):
        if self._after_pil is None:
            return
        self._mode = "compare"
        self._split_x = 0.5
        self._update_toggle_style()
        self._redraw()

    def _update_toggle_style(self):
        if self._mode == "single":
            self._btn_single.configure(bg=C_ACCENT,      fg="#000000")
            self._btn_compare.configure(bg=C_BG_SURFACE, fg=C_TEXT_MUTED)
        else:
            self._btn_single.configure(bg=C_BG_SURFACE,  fg=C_TEXT_MUTED)
            self._btn_compare.configure(bg=C_ACCENT,     fg="#000000")

    # ════════════════════════════════════════════
    #  Drawing
    # ════════════════════════════════════════════

    def _redraw(self) -> None:
        self.canvas.delete("all")

        if self._before_pil is None:
            self._draw_placeholder()
            return

        cw = max(self.canvas.winfo_width(),  1)
        ch = max(self.canvas.winfo_height(), 1)

        if self._mode == "single" or self._after_pil is None:
            self._draw_single(cw, ch)
        else:
            self._draw_compare(cw, ch)

    def _draw_single(self, cw: int, ch: int) -> None:
        img = self._fit(self._before_pil, cw, ch)
        self._before_ref = ImageTk.PhotoImage(img)
        self.canvas.create_image(cw // 2, ch // 2,
                                 image=self._before_ref, anchor="center")

    def _draw_compare(self, cw: int, ch: int) -> None:
        """
        Crop-based split: left side shows before, right side shows after.
        Both images are fitted to the same canvas size first, then cropped.
        """
        split = int(cw * self._split_x)

        # Fit both images to the same canvas dimensions
        before_fit = self._fit(self._before_pil, cw, ch)
        after_fit  = self._fit(self._after_pil,  cw, ch)

        iw, ih = before_fit.size
        # Offset to center the image on canvas
        ox = (cw - iw) // 2
        oy = (ch - ih) // 2

        # Crop split relative to image coordinates
        img_split = max(0, min(iw, split - ox))

        # Left portion of BEFORE
        if img_split > 0:
            left_crop = before_fit.crop((0, 0, img_split, ih))
            self._before_ref = ImageTk.PhotoImage(left_crop)
            self.canvas.create_image(ox, oy,
                                     image=self._before_ref, anchor="nw")

        # Right portion of AFTER
        if img_split < iw:
            right_crop = after_fit.crop((img_split, 0, iw, ih))
            self._after_ref = ImageTk.PhotoImage(right_crop)
            self.canvas.create_image(ox + img_split, oy,
                                     image=self._after_ref, anchor="nw")

        # Divider line (full canvas height)
        self.canvas.create_line(split, 0, split, ch, fill=C_ACCENT, width=2)

        # Handle circle
        r = 14
        cy = ch // 2
        self.canvas.create_oval(
            split - r, cy - r, split + r, cy + r,
            fill=C_ACCENT, outline="white", width=2,
        )
        self.canvas.create_text(
            split, cy, text="⇔", fill="white",
            font=("Segoe UI", 9, "bold"),
        )

        # Badges
        self._draw_badge(ox + 8,        oy + 8, "ÖNCE")
        self._draw_badge(ox + iw - 8,   oy + 8, "SONRA", right=True)

    # ── Helpers ─────────────────────────────────

    @staticmethod
    def _fit(img: Image.Image, cw: int, ch: int) -> Image.Image:
        """Resize PIL image to fit within (cw, ch) preserving aspect ratio."""
        ratio = min(cw / img.width, ch / img.height)
        nw = max(1, int(img.width  * ratio))
        nh = max(1, int(img.height * ratio))
        return img.resize((nw, nh), Image.LANCZOS)

    def _draw_badge(self, x: int, y: int, text: str, right: bool = False) -> None:
        pad_x, pad_y = 8, 4
        char_w = 7
        tw = len(text) * char_w + pad_x * 2
        th = 14 + pad_y * 2

        rx1 = (x - tw) if right else x
        rx2 = x if right else (x + tw)
        ry1, ry2 = y, y + th

        self.canvas.create_rectangle(
            rx1, ry1, rx2, ry2,
            fill="#1a1a1a", outline=C_ACCENT, width=1,
        )
        self.canvas.create_text(
            (rx1 + rx2) // 2, (ry1 + ry2) // 2,
            text=text, fill="white",
            font=("Segoe UI", 8, "bold"),
        )

    def _draw_placeholder(self) -> None:
        cw = self.canvas.winfo_width()  or 600
        ch = self.canvas.winfo_height() or 400
        cx, cy = cw // 2, ch // 2
        pad = 40
        self.canvas.create_rectangle(
            pad, pad, cw - pad, ch - pad,
            outline=C_BORDER, dash=(6, 4), width=1,
        )
        self.canvas.create_text(cx, cy - 16, text="🖼",
                                font=("Segoe UI Emoji", 28), fill=C_TEXT_DIM)
        self.canvas.create_text(cx, cy + 20,
                                text="Görsel seçin veya buraya sürükleyin",
                                font=("Segoe UI", 10), fill=C_TEXT_DIM)

    # ════════════════════════════════════════════
    #  Drag
    # ════════════════════════════════════════════

    def _on_press(self, event):
        if self._mode != "compare":
            return
        split = int(self.canvas.winfo_width() * self._split_x)
        if abs(event.x - split) < 24:
            self._dragging = True
            self.canvas.configure(cursor="sb_h_double_arrow")

    def _on_drag(self, event):
        if not self._dragging:
            return
        cw = max(self.canvas.winfo_width(), 1)
        self._split_x = max(0.02, min(0.98, event.x / cw))
        self._redraw()

    def _on_release(self, event):
        self._dragging = False
        self.canvas.configure(cursor="crosshair")

    def _on_resize(self, event=None):
        self._redraw()

    # ════════════════════════════════════════════
    #  Widget factory
    # ════════════════════════════════════════════

    def _make_toggle(self, master, text, command):
        return Button(
            master, text=text, command=command,
            bg=C_BG_SURFACE, fg=C_TEXT_MUTED,
            relief="flat", bd=0,
            font=("Segoe UI", 8, "bold"),
            cursor="hand2", padx=10, pady=3,
        )

    # ════════════════════════════════════════════
    #  Theme
    # ════════════════════════════════════════════

    def apply_theme(self, element_bg, border_color) -> None:
        self.canvas.configure(bg=element_bg)
        self._redraw()
