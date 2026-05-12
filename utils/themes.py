"""
5 tema paleti tanımları.
ThemePalette dataclass ve tüm tema örnekleri burada.
"""

from dataclasses import dataclass


@dataclass
class ThemePalette:
    name: str
    display_name: str
    bg_base: str
    bg_surface: str
    bg_raised: str
    bg_input: str
    bg_hover: str
    border: str
    text: str
    text_muted: str
    accent: str
    accent_dim: str
    log_fg: str
    btn_fg: str = "#000000"   # foreground for accent buttons


DARK = ThemePalette(
    name="dark",
    display_name="🌙 Koyu",
    bg_base="#0f0f0f",
    bg_surface="#161616",
    bg_raised="#1e1e1e",
    bg_input="#252525",
    bg_hover="#2a2a2a",
    border="#2d2d2d",
    text="#e8e8e8",
    text_muted="#888888",
    accent="#00c896",
    accent_dim="#009e78",
    log_fg="#39d98a",
)

LIGHT = ThemePalette(
    name="light",
    display_name="☀ Açık",
    bg_base="#f5f5f5",
    bg_surface="#ebebeb",
    bg_raised="#ffffff",
    bg_input="#ffffff",
    bg_hover="#dcdcdc",
    border="#cccccc",
    text="#1a1a1a",
    text_muted="#666666",
    accent="#007a50",
    accent_dim="#005a3a",
    log_fg="#007a50",
    btn_fg="#ffffff",
)

PURPLE = ThemePalette(
    name="purple",
    display_name="💜 Mor",
    bg_base="#120820",
    bg_surface="#1e1030",
    bg_raised="#2a1845",
    bg_input="#321d52",
    bg_hover="#3d2460",
    border="#4a2d70",
    text="#e8d8ff",
    text_muted="#9b7ec8",
    accent="#b06aff",
    accent_dim="#8040e0",
    log_fg="#c890ff",
)

OCEAN = ThemePalette(
    name="ocean",
    display_name="🌊 Okyanus",
    bg_base="#050e1a",
    bg_surface="#0a1828",
    bg_raised="#0f2240",
    bg_input="#142a50",
    bg_hover="#1a3460",
    border="#1e3d70",
    text="#d0e8ff",
    text_muted="#6090c0",
    accent="#00a8ff",
    accent_dim="#0080cc",
    log_fg="#40c0ff",
)

FOREST = ThemePalette(
    name="forest",
    display_name="🌿 Orman",
    bg_base="#050f05",
    bg_surface="#0a180a",
    bg_raised="#102010",
    bg_input="#142814",
    bg_hover="#1a3020",
    border="#1e3820",
    text="#d0f0d0",
    text_muted="#60a060",
    accent="#27ae60",
    accent_dim="#1e8a48",
    log_fg="#40d080",
)

ALL_THEMES: dict[str, ThemePalette] = {
    "dark":   DARK,
    "light":  LIGHT,
    "purple": PURPLE,
    "ocean":  OCEAN,
    "forest": FOREST,
}

DEFAULT_THEME = "dark"
