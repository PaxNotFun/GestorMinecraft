import json
import os
import sys
from pathlib import Path

CURRENT_VERSION = "3.3.1"

# Directorio de datos de la aplicación multiplataforma
if sys.platform == "win32":
    APP_DIR = Path(os.getenv('APPDATA', Path.home() / "AppData" / "Roaming")) / "GetMineHub"
elif sys.platform == "darwin":
    APP_DIR = Path.home() / "Library" / "Application Support" / "GetMineHub"
else:
    # Linux y otros Unix
    APP_DIR = Path(os.getenv('XDG_CONFIG_HOME', Path.home() / ".config")) / "GetMineHub"
SERVERS_FILE_PATH = APP_DIR / "servers.json"
SETTINGS_FILE_PATH = APP_DIR / "settings.json"
JAVA_RUNTIMES_DIR = APP_DIR / "java_runtimes"

DARK_BG = "#0a0a0f"
CARD_BG = "#13131a"
CARD_BG_HOVER = "#1a1a24"
ACCENT = "#8b5cf6"
ACCENT_HOVER = "#a78bfa"
SECONDARY = "#6366f1"
TEXT_LIGHT = "#f1f5f9"
TEXT_MUTED = "#94a3b8"
SUCCESS = "#10b981"
SUCCESS_HOVER = "#34d399"
WARNING = "#f59e0b"
WARNING_HOVER = "#fbbf24"
DANGER = "#ef4444"
DANGER_HOVER = "#f87171"
BORDER = "#1e1e2e"
INPUT_BG = "#18181f"
INPUT_BORDER = "#2d2d3f"


def get_servers_base_dir():
    """Obtiene el directorio base de los servidores desde la configuración."""
    settings = load_all_settings()
    base_path_str = settings.get("servers_base_dir", str(APP_DIR / "servers"))
    return Path(os.path.expanduser(base_path_str))


def ensure_config_exists():
    """Asegura que todos los directorios y archivos de configuración existan."""
    APP_DIR.mkdir(parents=True, exist_ok=True)
    JAVA_RUNTIMES_DIR.mkdir(parents=True, exist_ok=True)
    get_servers_base_dir().mkdir(parents=True, exist_ok=True)

    if not SERVERS_FILE_PATH.exists():
        SERVERS_FILE_PATH.write_text(json.dumps([]), encoding='utf-8')
    if not SETTINGS_FILE_PATH.exists():
        from .defaults import DEFAULT_TIMEOUT
        default_settings = {
            "servers_base_dir": str(APP_DIR / "servers"),
            "max_ram_limit": 0,
            "check_for_updates": True,
            "timeout": DEFAULT_TIMEOUT
        }
        SETTINGS_FILE_PATH.write_text(json.dumps(default_settings, indent=4), encoding='utf-8')


def save_all_settings(settings_dict):
    """Guarda todo el diccionario de configuraciones."""
    with open(SETTINGS_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(settings_dict, f, indent=4)


def save_setting(key, value):
    """Guarda una configuración específica."""
    settings = load_all_settings()
    settings[key] = value
    save_all_settings(settings)


def load_all_settings():
    """Carga todas las configuraciones."""
    try:
        with open(SETTINGS_FILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def load_setting(key, default=None):
    """Carga una configuración específica."""
    return load_all_settings().get(key, default)