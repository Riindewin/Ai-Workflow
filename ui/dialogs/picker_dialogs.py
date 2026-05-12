from tkinter import filedialog, colorchooser


def ask_open_files():
    return filedialog.askopenfilenames()


def ask_directory():
    return filedialog.askdirectory()


def ask_color(initial_color="#000000"):
    color = colorchooser.askcolor(initialcolor=initial_color)
    return color[1] if color else None
