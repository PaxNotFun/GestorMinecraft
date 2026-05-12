from tkinter import messagebox

import customtkinter as ctk

from config.general import ensure_config_exists
from ui.main_window import MainWindow
from utils.version_checker import check_and_force_update
from utils.windows_helper import set_dpi_awareness


class App:
    """Clase principal de la aplicación."""

    def __init__(self):
        self.setup()
        self.window = MainWindow()

    def setup(self):
        """Configuración inicial de la aplicación."""
        set_dpi_awareness()
        check_and_force_update()
        ensure_config_exists()
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

    def run(self):
        """Ejecuta el mainloop de la aplicación."""
        try:
            self.window.mainloop()
        except Exception as e:
            messagebox.showerror("Error Fatal", f"Error inesperado:\n{e}")