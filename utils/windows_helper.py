import ctypes
import sys


def set_dpi_awareness():
    """Ajusta la aplicación para que sea consciente del DPI en Windows."""
    if sys.platform == "win32":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except (AttributeError, OSError):
                pass


def apply_dark_title_bar(window):
    """Aplica la barra de título oscura en ventanas de Windows."""
    if sys.platform != "win32":
        return

    def _apply():
        try:
            window.update_idletasks()
            hwnd = window.winfo_id()
            if not hwnd:
                return
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            value = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(value), ctypes.sizeof(value)
            )
        except Exception:
            pass

    window.after(10, _apply)