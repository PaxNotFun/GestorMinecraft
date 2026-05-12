import sys


def safe_grab_set(window):
    """
    Ejecuta grab_set() de forma segura en todas las plataformas.
    En Linux/Mac, CTkToplevel no es visible aún cuando __init__ llama setup_window(),
    por lo que grab_set() falla con 'grab failed: window not viewable'.
    La solución es diferirlo con after() para que Tk procese los eventos pendientes primero.
    """
    if sys.platform == "win32":
        window.grab_set()
    else:
        window.after(100, lambda: window.grab_set() if window.winfo_exists() else None)
