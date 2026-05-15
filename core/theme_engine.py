"""
ThemeEngine — centralized theme management with animated transitions.

Usage:
    engine = ThemeEngine(root)
    engine.register(my_panel)   # panel must have apply_theme(palette) method
    engine.apply("purple")      # animated ~200ms transition
"""

import logging
from utils.themes import ThemePalette, ALL_THEMES, DEFAULT_THEME

logger = logging.getLogger("uic_app")


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return (128, 128, 128)
    try:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    except ValueError:
        return (128, 128, 128)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return "#{:02x}{:02x}{:02x}".format(
        max(0, min(255, r)),
        max(0, min(255, g)),
        max(0, min(255, b)),
    )


class ThemeEngine:

    THEMES = ALL_THEMES

    def __init__(self, root):
        self._root = root
        self._components: list = []
        self._current_name: str = DEFAULT_THEME
        self._animating: bool = False

    # ── Registration ─────────────────────────────

    def register(self, component) -> None:
        if component not in self._components:
            self._components.append(component)

    def unregister(self, component) -> None:
        if component in self._components:
            self._components.remove(component)

    # ── Apply ────────────────────────────────────

    def apply(self, theme_name: str, animated: bool = True) -> None:
        if theme_name not in self.THEMES:
            logger.warning("Unknown theme: %s", theme_name)
            return

        from_palette = self.THEMES[self._current_name]
        to_palette   = self.THEMES[theme_name]
        self._current_name = theme_name

        if animated and not self._animating:
            self._animate(from_palette, to_palette)
        else:
            self._apply_palette(to_palette)

    def current(self) -> ThemePalette:
        return self.THEMES[self._current_name]

    def current_name(self) -> str:
        return self._current_name

    # ── Animation ────────────────────────────────

    def _animate(self, from_p: ThemePalette, to_p: ThemePalette,
                 steps: int = 10, interval_ms: int = 20) -> None:
        self._animating = True
        self._anim_step(from_p, to_p, 0, steps, interval_ms)

    def _anim_step(self, from_p: ThemePalette, to_p: ThemePalette,
                   step: int, total: int, interval_ms: int) -> None:
        if step > total:
            self._animating = False
            self._apply_palette(to_p)
            return

        t = step / total
        mid = self._interpolate_palette(from_p, to_p, t)
        self._apply_palette(mid)
        self._root.after(interval_ms,
                         lambda: self._anim_step(from_p, to_p, step + 1, total, interval_ms))

    # ── Palette application ───────────────────────

    def _apply_palette(self, palette: ThemePalette) -> None:
        for component in list(self._components):
            try:
                component.apply_theme(palette)
            except Exception as exc:
                logger.debug("apply_theme failed for %s: %s", component, exc)

    # ── Interpolation ─────────────────────────────

    @staticmethod
    def interpolate_color(c1: str, c2: str, t: float) -> str:
        """Interpolate between two hex colors. t=0 → c1, t=1 → c2."""
        t = max(0.0, min(1.0, t))
        r1, g1, b1 = _hex_to_rgb(c1)
        r2, g2, b2 = _hex_to_rgb(c2)
        return _rgb_to_hex(
            int(r1 + (r2 - r1) * t),
            int(g1 + (g2 - g1) * t),
            int(b1 + (b2 - b1) * t),
        )

    @classmethod
    def _interpolate_palette(cls, p1: ThemePalette, p2: ThemePalette,
                              t: float) -> ThemePalette:
        ic = cls.interpolate_color
        return ThemePalette(
            name=p2.name,
            display_name=p2.display_name,
            bg_base    = ic(p1.bg_base,    p2.bg_base,    t),
            bg_surface = ic(p1.bg_surface, p2.bg_surface, t),
            bg_raised  = ic(p1.bg_raised,  p2.bg_raised,  t),
            bg_input   = ic(p1.bg_input,   p2.bg_input,   t),
            bg_hover   = ic(p1.bg_hover,   p2.bg_hover,   t),
            border     = ic(p1.border,     p2.border,     t),
            text       = ic(p1.text,       p2.text,       t),
            text_muted = ic(p1.text_muted, p2.text_muted, t),
            accent     = ic(p1.accent,     p2.accent,     t),
            accent_dim = ic(p1.accent_dim, p2.accent_dim, t),
            log_fg     = ic(p1.log_fg,     p2.log_fg,     t),
            btn_fg     = ic(p1.btn_fg,     p2.btn_fg,     t),
        )
