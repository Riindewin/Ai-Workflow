"""
Toast — kısa süreli bildirim penceresi.
Ekranın sağ alt köşesinde görünür, otomatik kapanır.
"""

import tkinter as tk


class Toast:

    @staticmethod
    def show(
        root: tk.Tk,
        message: str,
        duration_ms: int = 3000,
        color: str = "#27ae60",
    ) -> None:
        """Sağ alt köşede toast bildirimi göster."""
        try:
            win = tk.Toplevel(root)
            win.overrideredirect(True)  # Başlık çubuğu yok
            win.attributes("-topmost", True)
            win.configure(bg=color)

            lbl = tk.Label(
                win,
                text=message,
                bg=color,
                fg="white",
                font=("Segoe UI", 9, "bold"),
                padx=16,
                pady=10,
            )
            lbl.pack()

            # Konumlandır: sağ alt köşe
            win.update_idletasks()
            w = win.winfo_reqwidth()
            h = win.winfo_reqheight()
            sw = root.winfo_screenwidth()
            sh = root.winfo_screenheight()
            x = sw - w - 20
            y = sh - h - 60
            win.geometry(f"+{x}+{y}")

            # Otomatik kapat
            win.after(duration_ms, win.destroy)

            # Tıklanınca kapat
            lbl.bind("<Button-1>", lambda e: win.destroy())
            win.bind("<Button-1>", lambda e: win.destroy())

        except Exception:
            pass  # Toast hatası uygulamayı etkilememeli
