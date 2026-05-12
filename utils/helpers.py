import sys
import socket

from packaging import version


def compare_versions(v1, v2):
    """Compara dos strings de versión."""
    try:
        return version.parse(v1) > version.parse(v2)
    except Exception:
        return v1 > v2


def center_window(window, width=0, height=0):
    """Centra la ventana en la pantalla de forma precisa."""
    window.update_idletasks()

    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    if width > 0 and height > 0:
        target_width = width
        target_height = height
        window.geometry(f'{width}x{height}')
    else:
        target_width = window.winfo_width()
        target_height = window.winfo_height()

    x = int((screen_width / 2) - (target_width / 2))
    y = int((screen_height / 2) - (target_height / 2))

    window.geometry(f'+{x}+{y}')


def fix_scroll_linux(scroll_frame):
    """
    Corrige el scroll con rueda del ratón en Linux para CTkScrollableFrame.

    Causa raíz: CTkScrollableFrame configura yscrollincrement=1 en Windows
    y pasa delta/6 (~20) units por tick = ~20px de scroll suave.
    En Linux no configura yscrollincrement (queda en 0), lo que hace que
    cada "unit" sea 1/10 de la altura visible = salto enorme.

    Solución: replicar exactamente el comportamiento de Windows:
      - yscrollincrement=1  (1px por unit, igual que Windows)
      - scroll de 20 units por tick  (= 20px, igual que Windows)
      - Enter/Leave para no disparar en todos los frames a la vez
    """
    if not sys.platform.startswith("linux"):
        return

    canvas = scroll_frame._parent_canvas
    # Igual que CTk en Windows: 1px por unit
    canvas.configure(yscrollincrement=1)

    def _on_mousewheel(event):
        if event.num == 4:
            canvas.yview_scroll(-20, "units")  # 20px hacia arriba
        elif event.num == 5:
            canvas.yview_scroll(20, "units")   # 20px hacia abajo

    def _bind_mousewheel(event):
        canvas.bind_all("<Button-4>", _on_mousewheel)
        canvas.bind_all("<Button-5>", _on_mousewheel)

    def _unbind_mousewheel(event):
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")

    canvas.bind("<Enter>", _bind_mousewheel)
    canvas.bind("<Leave>", _unbind_mousewheel)
    scroll_frame.bind("<Enter>", _bind_mousewheel)
    scroll_frame.bind("<Leave>", _unbind_mousewheel)


def check_internet_connection(host="8.8.8.8", port=53, timeout=3):
    """Comprueba si hay conexión a internet."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.close()
        return True
    except socket.error:
        return False
