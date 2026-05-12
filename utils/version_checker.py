import sys
import webbrowser
from tkinter import messagebox

import customtkinter as ctk
import requests
from packaging import version

from config.defaults import DEFAULT_TIMEOUT
from config.general import CURRENT_VERSION, load_setting  # IMPORTAR load_setting
from config.urls import VERSION_JSON_URL, DOWNLOAD_URL
from utils.windows_helper import apply_dark_title_bar


def get_latest_version():
    """Obtiene la última versión disponible desde el repositorio."""
    try:
        response = requests.get(VERSION_JSON_URL, timeout=DEFAULT_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            return data.get("version", CURRENT_VERSION)
        return None
    except Exception:
        return None


def compare_versions(v1, v2):
    """Compara dos versiones."""
    try:
        return version.parse(v1) > version.parse(v2)
    except Exception:
        return v1 > v2


def check_and_force_update():
    """Verifica y fuerza la actualización si es necesaria."""
    if not load_setting("check_for_updates", default=True):
        return

    latest_version = get_latest_version()

    if not latest_version:
        return

    if compare_versions(latest_version, CURRENT_VERSION):
        root_temp = ctk.CTk()
        apply_dark_title_bar(root_temp)
        root_temp.withdraw()
        root_temp.attributes("-topmost", True)

        msg = (
            f"Se requiere actualización obligatoria!\n\n"
            f"Versión instalada: {CURRENT_VERSION}\n"
            f"Nueva versión disponible: {latest_version}\n\n"
            "¿Quieres ir a la página de descarga ahora?"
        )

        if messagebox.askyesno("Actualización Requerida", msg, icon="question", parent=root_temp):
            webbrowser.open(DOWNLOAD_URL)
            sys.exit(0)
        else:
            messagebox.showwarning(
                "Actualización Necesaria",
                "La aplicación se cerrará ya que se requiere la actualización.",
                parent=root_temp
            )
            sys.exit(0)

        root_temp.destroy()