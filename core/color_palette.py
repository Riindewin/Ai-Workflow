"""
ColorPalette — extract dominant colors from a PIL Image.
Uses k-means style quantization via Pillow's quantize().
"""

import logging
from PIL import Image

logger = logging.getLogger("uic_app")


class ColorPalette:

    @staticmethod
    def extract(img: Image.Image, n_colors: int = 6) -> list[tuple[int, int, int]]:
        """
        Extract n_colors dominant colors from the image.
        Returns list of (R, G, B) tuples sorted by frequency (most dominant first).
        """
        try:
            # Resize for speed
            thumb = img.copy().convert("RGB")
            thumb.thumbnail((200, 200))

            # Quantize to n_colors
            quantized = thumb.quantize(colors=n_colors, method=Image.Quantize.MEDIANCUT)
            palette_data = quantized.getpalette()[:n_colors * 3]

            colors = []
            for i in range(n_colors):
                r = palette_data[i * 3]
                g = palette_data[i * 3 + 1]
                b = palette_data[i * 3 + 2]
                colors.append((r, g, b))

            return colors

        except Exception as exc:
            logger.error("Color palette extraction failed: %s", exc)
            return [(128, 128, 128)] * n_colors

    @staticmethod
    def to_hex(color: tuple[int, int, int]) -> str:
        return "#{:02x}{:02x}{:02x}".format(*color)

    @staticmethod
    def extract_hex(img: Image.Image, n_colors: int = 6) -> list[str]:
        return [ColorPalette.to_hex(c) for c in ColorPalette.extract(img, n_colors)]

    @staticmethod
    def get_palette(img: Image.Image, n: int = 6) -> list[str]:
        """Görselin baskın n rengini hex string listesi olarak döndür."""
        rgb = img.convert("RGB").resize((100, 100), Image.LANCZOS)
        pixels = list(rgb.getdata())
        from collections import Counter
        counts = Counter(pixels)
        top = [color for color, _ in counts.most_common(n * 10)]
        # Basit kümeleme: birbirine yakın renkleri birleştir
        palette = []
        for r, g, b in top:
            if len(palette) >= n:
                break
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            # Mevcut palette'deki renklerden yeterince farklı mı?
            too_close = False
            for existing in palette:
                er = int(existing[1:3], 16)
                eg = int(existing[3:5], 16)
                eb = int(existing[5:7], 16)
                dist = abs(r - er) + abs(g - eg) + abs(b - eb)
                if dist < 60:
                    too_close = True
                    break
            if not too_close:
                palette.append(hex_color)
        return palette
