"""
ZoomPanCanvas — replaces PreviewPanel.

Features:
  - Zoom (mouse wheel, 10%–1000%)
  - Pan (left-drag when crop mode off)
  - Before/After comparison slider (always active when both images present)
  - Crop mode (left-drag draws selection rectangle)
  - Pixel color indicator (mouse hover)
  - Minimap (visible when zoom > 100%)
  - RGB Histogram + Color Palette below canvas
"""

import logging
import os
from tkinter import Frame, Canvas, Label, Button, BOTH, X, LEFT, RIGHT, TOP, BOTTOM, HORIZONTAL
from PIL import Image, ImageTk

from utils.themes import ThemePalette, DARK

logger = logging.getLogger("uic_app")

MIN_ZOOM = 0.1
MAX_ZOOM = 10.0


class ZoomPanCanvas(Frame):

    def __init__(self, master, controller=None):
        super().__init__(master, bg=DARK.bg_raised)
        self.controller = controller
        self._palette = DARK

        # ── Toolbar ─────────────────────────────
        self._toolbar = Frame(self, bg=DARK.bg_raised, height=32)
        self._toolbar.pack(fill=X)
        self._toolbar.pack_propagate(False)

        Label(self._toolbar, text="ÖNİZLEME", bg=DARK.bg_raised,
              fg=DARK.text_muted, font=("Segoe UI", 8, "bold"), anchor="w"
              ).pack(side=LEFT, padx=12)

        self._zoom_label = Label(self._toolbar, text="100%", bg=DARK.bg_raised,
                                 fg=DARK.text_muted, font=("Segoe UI", 8))
        self._zoom_label.pack(side=RIGHT, padx=8)

        self._size_label = Label(self._toolbar, text="", bg=DARK.bg_raised,
                                 fg=DARK.text_muted, font=("Segoe UI", 8))
        self._size_label.pack(side=RIGHT, padx=8)

        self._single_view_btn = Button(
            self._toolbar, text="✕ Tek Görünüm", bg=DARK.bg_raised, fg=DARK.text_muted,
            relief="flat", bd=0, cursor="hand2", font=("Segoe UI", 8),
            command=self.clear_after,
        )
        # Başlangıçta gizli — show_comparison() çağrısında pack edilir

        self._reset_btn = Button(
            self._toolbar, text="⊡ Sıfırla", bg=DARK.bg_raised, fg=DARK.text_muted,
            relief="flat", bd=0, cursor="hand2", font=("Segoe UI", 8),
            command=self.reset_zoom,
        )
        self._reset_btn.pack(side=RIGHT, padx=4)

        Frame(self, bg=DARK.border, height=1).pack(fill=X)

        # ── Canvas ──────────────────────────────
        self.canvas = Canvas(self, bg=DARK.bg_input, highlightthickness=0,
                             cursor="crosshair")
        self.canvas.pack(fill=BOTH, expand=True, padx=8, pady=8)

        # ── Histogram + Palette bar ──────────────────
        self._hist_bar = Frame(self, bg=DARK.bg_surface, height=64)
        self._hist_bar.pack(fill=X)
        self._hist_bar.pack_propagate(False)

        self._hist_canvas = Canvas(self._hist_bar, bg=DARK.bg_surface,
                                   highlightthickness=0, height=44)
        self._hist_canvas.pack(side=LEFT, fill=X, expand=True, padx=4, pady=4)

        self._palette_frame = Frame(self._hist_bar, bg=DARK.bg_surface)
        self._palette_frame.pack(side=RIGHT, padx=4, pady=4)

        self._hist_job = None  # pending after() id

        # ── Pixel color bar ──────────────────────
        self._pixel_bar = Frame(self, bg=DARK.bg_surface, height=22)
        self._pixel_bar.pack(fill=X)
        self._pixel_bar.pack_propagate(False)
        self._pixel_swatch = Frame(self._pixel_bar, bg=DARK.bg_surface, width=16, height=16)
        self._pixel_swatch.pack(side=LEFT, padx=(8, 4), pady=3)
        self._pixel_label = Label(self._pixel_bar, text="", bg=DARK.bg_surface,
                                  fg=DARK.text_muted, font=("Consolas", 8))
        self._pixel_label.pack(side=LEFT)

        # ── State ───────────────────────────────
        self._zoom: float = 1.0
        self._offset_x: float = 0.0
        self._offset_y: float = 0.0

        self._before_pil: Image.Image | None = None
        self._after_pil:  Image.Image | None = None
        self._before_ref = None
        self._after_ref  = None
        # Fix #20: cache RGB version of before_pil to avoid per-motion conversion
        self._before_rgb: Image.Image | None = None

        # Compare slider
        self._split_x: float = 0.5
        self._dragging_split = False

        # Pan
        self._pan_start: tuple | None = None

        # Crop
        self._crop_active = False
        self._crop_start:  tuple | None = None
        self._crop_end:    tuple | None = None
        self._crop_ratio:  str = "Serbest"

        # Minimap
        self._minimap_ref = None

        # Bindings
        self.canvas.bind("<Configure>",       self._on_resize)
        self.canvas.bind("<MouseWheel>",      self._on_wheel)
        self.canvas.bind("<Button-4>",        self._on_wheel)
        self.canvas.bind("<Button-5>",        self._on_wheel)
        self.canvas.bind("<ButtonPress-1>",   self._on_press)
        self.canvas.bind("<B1-Motion>",       self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>",          self._on_motion)
        self.canvas.bind("<Leave>",           self._on_leave)

    # ════════════════════════════════════════════
    #  Public API
    # ════════════════════════════════════════════

    def show_image(self, img: Image.Image, file_path: str = None) -> None:
        self._before_pil = img
        self._after_pil  = None
        # Fix #20: pre-compute RGB cache for pixel color indicator
        self._before_rgb = img.convert("RGB") if img.mode != "RGB" else img
        self._schedule_hist_update(img)
        # Boyut göstergesi güncelle
        try:
            size_text = f"{img.width}×{img.height}"
            if file_path and os.path.isfile(file_path):
                size_bytes = os.path.getsize(file_path)
                if size_bytes >= 1024 * 1024:
                    size_text += f" · {size_bytes / 1024 / 1024:.1f} MB"
                else:
                    size_text += f" · {size_bytes / 1024:.0f} KB"
            self._size_label.configure(text=size_text)
        except Exception:
            pass
        # Tek görünüm butonunu gizle
        try:
            self._single_view_btn.pack_forget()
        except Exception:
            pass
        self._redraw()

    def show_comparison(self, before: Image.Image, after: Image.Image) -> None:
        self._before_pil = before
        self._after_pil  = after
        self._split_x    = 0.5
        # Fix #20: update RGB cache
        self._before_rgb = before.convert("RGB") if before.mode != "RGB" else before
        self._schedule_hist_update(before)
        # Boyut göstergesi güncelle
        try:
            self._size_label.configure(
                text=f"ÖNCE: {before.width}×{before.height}  →  SONRA: {after.width}×{after.height}"
            )
        except Exception:
            pass
        # Tek görünüm butonunu göster
        try:
            self._single_view_btn.pack(side=RIGHT, padx=4)
        except Exception:
            pass
        self._redraw()

    def clear_after(self) -> None:
        self._after_pil = None
        # Restore RGB cache to before image
        if self._before_pil is not None:
            self._before_rgb = self._before_pil.convert("RGB") if self._before_pil.mode != "RGB" else self._before_pil
            self._schedule_hist_update(self._before_pil)
        # Tek görünüm butonunu gizle
        try:
            self._single_view_btn.pack_forget()
        except Exception:
            pass
        self._redraw()

    def reset_zoom(self) -> None:
        self._zoom     = 1.0
        self._offset_x = 0.0
        self._offset_y = 0.0
        self._redraw()

    def enable_crop_mode(self, ratio: str = "Serbest") -> None:
        self._crop_active = True
        self._crop_ratio  = ratio
        self._crop_start  = None
        self._crop_end    = None
        self.canvas.configure(cursor="crosshair")

    def disable_crop_mode(self) -> None:
        self._crop_active = False
        self._crop_start  = None
        self._crop_end    = None
        self.canvas.configure(cursor="crosshair")
        self._redraw()

    def get_crop_rect_normalized(self) -> tuple | None:
        """Return (x1,y1,x2,y2) in image-normalized [0,1] coords, or None."""
        if not (self._crop_start and self._crop_end and self._before_pil):
            return None
        cx1, cy1 = self._crop_start
        cx2, cy2 = self._crop_end
        if cx1 > cx2: cx1, cx2 = cx2, cx1
        if cy1 > cy2: cy1, cy2 = cy2, cy1

        ix1, iy1 = self._canvas_to_image(cx1, cy1)
        ix2, iy2 = self._canvas_to_image(cx2, cy2)

        w, h = self._before_pil.width, self._before_pil.height
        nx1 = max(0.0, min(1.0, ix1 / w))
        ny1 = max(0.0, min(1.0, iy1 / h))
        nx2 = max(0.0, min(1.0, ix2 / w))
        ny2 = max(0.0, min(1.0, iy2 / h))

        if nx2 - nx1 < 0.001 or ny2 - ny1 < 0.001:
            return None
        return (nx1, ny1, nx2, ny2)

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

        if self._after_pil is not None:
            self._draw_compare(cw, ch)
        else:
            self._draw_single(cw, ch)

        if self._crop_active and self._crop_start and self._crop_end:
            self._draw_crop_rect()

        if self._zoom > 1.01:
            self._draw_minimap(cw, ch)

        self._zoom_label.configure(text=f"{int(self._zoom * 100)}%")

    def _draw_single(self, cw: int, ch: int) -> None:
        img = self._render(self._before_pil, cw, ch)
        self._before_ref = ImageTk.PhotoImage(img)
        ox, oy = self._image_origin(cw, ch, img.width, img.height)
        self.canvas.create_image(ox, oy, image=self._before_ref, anchor="nw")

    def _draw_compare(self, cw: int, ch: int) -> None:
        split = int(cw * self._split_x)

        before_r = self._render(self._before_pil, cw, ch)
        after_r  = self._render(self._after_pil,  cw, ch)

        iw, ih = before_r.size
        ox, oy = self._image_origin(cw, ch, iw, ih)
        img_split = max(0, min(iw, split - ox))

        # Left: before
        if img_split > 0:
            left = before_r.crop((0, 0, img_split, ih))
            self._before_ref = ImageTk.PhotoImage(left)
            self.canvas.create_image(ox, oy, image=self._before_ref, anchor="nw")

        # Right: after
        if img_split < iw:
            right = after_r.crop((img_split, 0, iw, ih))
            self._after_ref = ImageTk.PhotoImage(right)
            self.canvas.create_image(ox + img_split, oy, image=self._after_ref, anchor="nw")

        # Divider
        self.canvas.create_line(split, 0, split, ch,
                                fill=self._palette.accent, width=2)
        r = 14
        cy = ch // 2
        self.canvas.create_oval(split-r, cy-r, split+r, cy+r,
                                fill=self._palette.accent, outline="white", width=2)
        self.canvas.create_text(split, cy, text="⇔", fill="white",
                                font=("Segoe UI", 9, "bold"))

        # Badges
        self._badge(ox + 8,      oy + 8, "ÖNCE")
        self._badge(ox + iw - 8, oy + 8, "SONRA", right=True)

        # Boyut bilgisi
        try:
            before_size = f"{self._before_pil.width}×{self._before_pil.height}"
            after_size  = f"{self._after_pil.width}×{self._after_pil.height}"
            self.canvas.create_text(ox + 8, oy + 32, text=before_size,
                                    fill=self._palette.text_muted,
                                    font=("Segoe UI", 7), anchor="w")
            self.canvas.create_text(ox + iw - 8, oy + 32, text=after_size,
                                    fill=self._palette.text_muted,
                                    font=("Segoe UI", 7), anchor="e")
        except Exception:
            pass

    def _draw_crop_rect(self) -> None:
        x1, y1 = self._crop_start
        x2, y2 = self._crop_end
        if x1 > x2: x1, x2 = x2, x1
        if y1 > y2: y1, y2 = y2, y1
        self.canvas.create_rectangle(x1, y1, x2, y2,
                                     outline=self._palette.accent,
                                     dash=(4, 3), width=2)

    def _draw_minimap(self, cw: int, ch: int) -> None:
        if self._before_pil is None:
            return
        mm_w, mm_h = 120, 90
        thumb = self._before_pil.copy()
        thumb.thumbnail((mm_w, mm_h))
        self._minimap_ref = ImageTk.PhotoImage(thumb)

        mx = cw - mm_w - 8
        my = ch - mm_h - 8
        self.canvas.create_rectangle(mx-2, my-2, mx+mm_w+2, my+mm_h+2,
                                     fill=self._palette.bg_surface,
                                     outline=self._palette.border)
        self.canvas.create_image(mx, my, image=self._minimap_ref, anchor="nw")

        # Viewport rect on minimap
        iw, ih = self._before_pil.width, self._before_pil.height
        tw, th = thumb.size
        sx = tw / iw
        sy = th / ih
        vx1 = mx + max(0, -self._offset_x) * sx / self._zoom
        vy1 = my + max(0, -self._offset_y) * sy / self._zoom
        vx2 = vx1 + (cw / self._zoom) * sx
        vy2 = vy1 + (ch / self._zoom) * sy
        self.canvas.create_rectangle(vx1, vy1, vx2, vy2,
                                     outline=self._palette.accent, width=1)

    def _draw_placeholder(self) -> None:
        cw = self.canvas.winfo_width()  or 600
        ch = self.canvas.winfo_height() or 400
        cx, cy = cw // 2, ch // 2
        self.canvas.create_rectangle(40, 40, cw-40, ch-40,
                                     outline=self._palette.border, dash=(6, 4), width=1)
        self.canvas.create_text(cx, cy-16, text="🖼",
                                font=("Segoe UI Emoji", 28), fill=self._palette.text_muted)
        self.canvas.create_text(cx, cy+20,
                                text="Görsel seçin veya buraya sürükleyin",
                                font=("Segoe UI", 10), fill=self._palette.text_muted)

    def _badge(self, x: int, y: int, text: str, right: bool = False) -> None:
        pad = 8
        tw = len(text) * 7 + pad * 2
        th = 20
        rx1 = (x - tw) if right else x
        rx2 = x if right else (x + tw)
        self.canvas.create_rectangle(rx1, y, rx2, y+th,
                                     fill=self._palette.bg_base, outline=self._palette.accent, width=1)
        self.canvas.create_text((rx1+rx2)//2, y+th//2, text=text,
                                fill=self._palette.text, font=("Segoe UI", 8, "bold"))

    # ════════════════════════════════════════════
    #  Rendering helpers
    # ════════════════════════════════════════════

    def _render(self, img: Image.Image, cw: int, ch: int) -> Image.Image:
        """Fit image to canvas, apply zoom and offset."""
        base_ratio = min(cw / img.width, ch / img.height)
        nw = max(1, int(img.width  * base_ratio * self._zoom))
        nh = max(1, int(img.height * base_ratio * self._zoom))
        return img.resize((nw, nh), Image.LANCZOS)

    def _image_origin(self, cw: int, ch: int, iw: int, ih: int) -> tuple[int, int]:
        base_ox = (cw - iw) // 2
        base_oy = (ch - ih) // 2
        return int(base_ox + self._offset_x), int(base_oy + self._offset_y)

    def _canvas_to_image(self, cx: float, cy: float) -> tuple[float, float]:
        """Convert canvas pixel coords to source image pixel coords."""
        if self._before_pil is None:
            return (0.0, 0.0)
        cw = max(self.canvas.winfo_width(),  1)
        ch = max(self.canvas.winfo_height(), 1)
        base_ratio = min(cw / self._before_pil.width, ch / self._before_pil.height)
        rendered_w = self._before_pil.width  * base_ratio * self._zoom
        rendered_h = self._before_pil.height * base_ratio * self._zoom
        ox = (cw - rendered_w) / 2 + self._offset_x
        oy = (ch - rendered_h) / 2 + self._offset_y
        ix = (cx - ox) / (base_ratio * self._zoom)
        iy = (cy - oy) / (base_ratio * self._zoom)
        return (ix, iy)

    # ════════════════════════════════════════════
    #  Event handlers
    # ════════════════════════════════════════════

    def _on_resize(self, _=None) -> None:
        self._redraw()

    def _on_wheel(self, event) -> None:
        if event.num == 4 or event.delta > 0:
            factor = 1.1
        else:
            factor = 1 / 1.1

        new_zoom = max(MIN_ZOOM, min(MAX_ZOOM, self._zoom * factor))
        if new_zoom == self._zoom:
            return

        # Zoom toward mouse position
        mx, my = event.x, event.y
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        cx, cy = cw / 2, ch / 2
        self._offset_x = (self._offset_x - (mx - cx)) * (new_zoom / self._zoom) + (mx - cx)
        self._offset_y = (self._offset_y - (my - cy)) * (new_zoom / self._zoom) + (my - cy)
        self._zoom = new_zoom
        self._redraw()

    def _on_press(self, event) -> None:
        if self._after_pil is not None:
            # Check if near split line
            split = int(self.canvas.winfo_width() * self._split_x)
            if abs(event.x - split) < 20:
                self._dragging_split = True
                return

        if self._crop_active:
            self._crop_start = (event.x, event.y)
            self._crop_end   = (event.x, event.y)
        else:
            self._pan_start = (event.x, event.y)

    def _on_drag(self, event) -> None:
        if self._dragging_split:
            cw = max(self.canvas.winfo_width(), 1)
            self._split_x = max(0.02, min(0.98, event.x / cw))
            self._redraw()
            return

        if self._crop_active and self._crop_start:
            cx, cy = event.x, event.y
            # Sabit oran kısıtlaması
            if hasattr(self, "_crop_ratio") and self._crop_ratio != "Serbest":
                try:
                    parts = self._crop_ratio.split(":")
                    ratio_w, ratio_h = float(parts[0]), float(parts[1])
                    dx = cx - self._crop_start[0]
                    dy = cy - self._crop_start[1]
                    # En büyük boyutu baz al
                    if abs(dx) > abs(dy):
                        dy = dx * ratio_h / ratio_w
                    else:
                        dx = dy * ratio_w / ratio_h
                    cx = self._crop_start[0] + dx
                    cy = self._crop_start[1] + dy
                except Exception:
                    pass
            self._crop_end = (cx, cy)
            self._redraw()
        elif self._pan_start:
            dx = event.x - self._pan_start[0]
            dy = event.y - self._pan_start[1]
            self._offset_x += dx
            self._offset_y += dy
            self._pan_start = (event.x, event.y)
            self._redraw()

    def _on_release(self, event) -> None:
        self._dragging_split = False
        self._pan_start = None

    def _on_motion(self, event) -> None:
        if self._before_pil is None:
            return
        ix, iy = self._canvas_to_image(event.x, event.y)
        ix, iy = int(ix), int(iy)
        if 0 <= ix < self._before_pil.width and 0 <= iy < self._before_pil.height:
            try:
                # Fix #20: use cached RGB image instead of converting on every move
                rgb = self._before_rgb if self._before_rgb is not None else self._before_pil.convert("RGB")
                pixel = rgb.getpixel((ix, iy))
                r, g, b = pixel[:3]
                hex_color = "#{:02x}{:02x}{:02x}".format(r, g, b)
                self._pixel_swatch.configure(bg=hex_color)
                self._pixel_label.configure(
                    text=f"{hex_color.upper()}  rgb({r}, {g}, {b})"
                )
            except Exception:
                pass
        else:
            self._on_leave()

    def _on_leave(self, _=None) -> None:
        self._pixel_swatch.configure(bg=self._palette.bg_surface)
        self._pixel_label.configure(text="")

    # ════════════════════════════════════════════
    #  Histogram & Palette
    # ════════════════════════════════════════════

    def _schedule_hist_update(self, img: Image.Image) -> None:
        """Histogram güncellemesini debounce ile zamanla."""
        if self._hist_job is not None:
            try:
                self.after_cancel(self._hist_job)
            except Exception:
                pass
        img_ref = img  # closure için referans
        self._hist_job = self.after(200, lambda: self._update_hist(img_ref))

    def _update_hist(self, img: Image.Image) -> None:
        """RGB histogram ve renk paletini arka planda hesapla."""
        self._hist_job = None
        import threading
        threading.Thread(target=self._compute_hist, args=(img,), daemon=True).start()

    def _compute_hist(self, img: Image.Image) -> None:
        """Thread'de histogram hesapla, ana thread'de çiz."""
        try:
            rgb = img.convert("RGB").resize((200, 200), Image.LANCZOS)
            r_hist = [0] * 256
            g_hist = [0] * 256
            b_hist = [0] * 256
            for r, g, b in rgb.getdata():
                r_hist[r] += 1
                g_hist[g] += 1
                b_hist[b] += 1
            # Normalize
            max_val = max(max(r_hist), max(g_hist), max(b_hist), 1)
            r_norm = [v / max_val for v in r_hist]
            g_norm = [v / max_val for v in g_hist]
            b_norm = [v / max_val for v in b_hist]
            # Palette
            try:
                from core.color_palette import ColorPalette
                palette = ColorPalette.get_palette(rgb, n=6)
            except Exception:
                palette = []
            self.after(0, lambda: self._draw_hist(r_norm, g_norm, b_norm, palette))
        except Exception:
            pass

    def _draw_hist(self, r_norm, g_norm, b_norm, palette) -> None:
        """Ana thread'de histogram canvas'ına çiz."""
        try:
            self._hist_canvas.delete("all")
            w = max(self._hist_canvas.winfo_width(), 100)
            h = max(self._hist_canvas.winfo_height(), 40)
            bar_w = max(1, w // 256)
            colors = [("#e05555", r_norm), ("#27ae60", g_norm), ("#00a8ff", b_norm)]
            for color, norm in colors:
                for i, val in enumerate(norm):
                    x = int(i * w / 256)
                    bar_h = int(val * h * 0.9)
                    if bar_h > 0:
                        self._hist_canvas.create_rectangle(
                            x, h - bar_h, x + bar_w, h,
                            fill=color, outline="", stipple="gray50"
                        )
            # Palette renk kareleri
            for child in self._palette_frame.winfo_children():
                child.destroy()
            for hex_color in palette:
                f = Frame(self._palette_frame, bg=hex_color, width=14, height=14,
                          cursor="hand2")
                f.pack(side=LEFT, padx=1)
        except Exception:
            pass

    # ════════════════════════════════════════════
    #  Theme
    # ════════════════════════════════════════════

    def apply_theme(self, palette: ThemePalette) -> None:
        self._palette = palette
        self.configure(bg=palette.bg_raised)
        self._toolbar.configure(bg=palette.bg_raised)
        self.canvas.configure(bg=palette.bg_input)
        self._hist_bar.configure(bg=palette.bg_surface)
        self._hist_canvas.configure(bg=palette.bg_surface)
        self._palette_frame.configure(bg=palette.bg_surface)
        self._pixel_bar.configure(bg=palette.bg_surface)
        self._pixel_swatch.configure(bg=palette.bg_surface)
        self._pixel_label.configure(bg=palette.bg_surface, fg=palette.text_muted)
        self._zoom_label.configure(bg=palette.bg_raised, fg=palette.text_muted)
        self._reset_btn.configure(bg=palette.bg_raised, fg=palette.text_muted,
                                  activebackground=palette.bg_hover)
        self._size_label.configure(bg=palette.bg_raised, fg=palette.text_muted)
        self._single_view_btn.configure(bg=palette.bg_raised, fg=palette.text_muted,
                                        activebackground=palette.bg_hover)
        for child in self._toolbar.winfo_children():
            try:
                child.configure(bg=palette.bg_raised)
            except Exception:
                pass
        self._redraw()
