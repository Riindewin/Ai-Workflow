from PIL import Image


class RemBGService:

    @staticmethod
    def is_available() -> bool:
        """rembg kütüphanesinin yüklü olup olmadığını kontrol eder."""
        try:
            import rembg  # noqa: F401
            return True
        except ImportError:
            return False

    @staticmethod
    def remove_background(image: Image.Image) -> Image.Image:
        """
        u2net modeli ile arka planı kaldırır.

        Raises:
            ImportError: rembg yüklü değilse.

        Returns:
            RGBA modunda PIL Image nesnesi.
        """
        from rembg import remove
        return remove(image)
