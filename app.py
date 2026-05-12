
from tkinterdnd2 import TkinterDnD
from ui.main_window import MainWindow

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = MainWindow(root)
    root.mainloop()
