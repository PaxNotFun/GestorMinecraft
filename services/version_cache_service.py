"""
Servicio de caché de versiones de servidores Minecraft.

Guarda en SQLite la lista de versiones por tipo, con TTL de 24 horas
expresado como timestamp Unix (entero). Sin fechas ISO, sin parsing raro.

Flujo:
  - Al arrancar la app se llama a prefetch_all_in_background()
  - Cualquier dropdown llama a get_versions(server_type) → instantáneo si hay caché
  - Si la caché expiró o falta, se descarga y se guarda
"""

import sqlite3
import threading
import time
from typing import Callable, Dict, List, Optional

import requests

from config.general import APP_DIR
from config.urls import (
    PAPERMC_API_URL, FOLIA_API_URL, VANILLA_API_URL,
    FORGE_API_URL, FABRIC_META_URL
)
from config.defaults import DEFAULT_TIMEOUT

DB_PATH = APP_DIR / "servers.db"
CACHE_TTL = 24 * 60 * 60          # 24 horas en segundos
HEADERS = {'User-Agent': 'GetMineHub'}

SERVER_TYPES = ["Vanilla", "PaperMC", "Folia", "Forge", "Fabric"]

# Caché en memoria para la sesión actual (evita ir a SQLite cada vez)
_memory_cache: Dict[str, List[str]] = {}
_memory_lock = threading.Lock()


# ── DB ────────────────────────────────────────────────────────────────────────

def _ensure_table():
    """Crea la tabla version_cache si no existe."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS version_cache (
                server_type TEXT PRIMARY KEY,
                versions     TEXT NOT NULL,
                fetched_at   INTEGER NOT NULL
            )
        """)
        conn.commit()


def _load_from_db(server_type: str) -> Optional[List[str]]:
    """Devuelve lista de versiones si existe y no ha expirado, si no None."""
    now = int(time.time())
    try:
        with sqlite3.connect(DB_PATH) as conn:
            row = conn.execute(
                "SELECT versions, fetched_at FROM version_cache WHERE server_type = ?",
                (server_type,)
            ).fetchone()
        if row and (now - row[1]) < CACHE_TTL:
            import json
            return json.loads(row[0])
    except Exception:
        pass
    return None


def _save_to_db(server_type: str, versions: List[str]):
    """Guarda versiones en DB con timestamp actual."""
    import json
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO version_cache (server_type, versions, fetched_at)
                   VALUES (?, ?, ?)""",
                (server_type, json.dumps(versions), int(time.time()))
            )
            conn.commit()
    except Exception:
        pass


# ── Fetch desde APIs ──────────────────────────────────────────────────────────

def _fetch_from_api(server_type: str) -> List[str]:
    """Descarga versiones desde la API correspondiente. Lanza excepción si falla."""
    if server_type == "Vanilla":
        r = requests.get(VANILLA_API_URL, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return [v['id'] for v in r.json()['versions'] if v['type'] == 'release']

    elif server_type == "PaperMC":
        r = requests.get(PAPERMC_API_URL, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return list(reversed(r.json().get("versions", [])))

    elif server_type == "Folia":
        r = requests.get(FOLIA_API_URL, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return list(reversed(r.json().get("versions", [])))

    elif server_type == "Fabric":
        r = requests.get(f"{FABRIC_META_URL}/versions/game", headers=HEADERS, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return [v['version'] for v in r.json() if v.get('stable', False)]

    elif server_type == "Forge":
        r = requests.get(FORGE_API_URL, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        promos = r.json().get('promos', {})
        seen, versions = set(), []
        for key in promos:
            mc_ver = key.rsplit('-', 1)[0]
            if mc_ver not in seen:
                seen.add(mc_ver)
                versions.append(mc_ver)
        versions.sort(key=lambda v: tuple(int(x) for x in v.split('.')), reverse=True)
        return versions

    return []


# ── API pública ───────────────────────────────────────────────────────────────

def get_versions(server_type: str) -> List[str]:
    """
    Devuelve versiones para un tipo. Orden de prioridad:
      1. Memoria (sesión actual)
      2. SQLite (si no expiró)
      3. API (bloquea el hilo llamante, guarda en DB y memoria)
    """
    with _memory_lock:
        if server_type in _memory_cache:
            return _memory_cache[server_type]

    db_versions = _load_from_db(server_type)
    if db_versions is not None:
        with _memory_lock:
            _memory_cache[server_type] = db_versions
        return db_versions

    # Fallback a API (solo si la caché no existe o expiró)
    try:
        versions = _fetch_from_api(server_type)
        if versions:
            _save_to_db(server_type, versions)
            with _memory_lock:
                _memory_cache[server_type] = versions
        return versions
    except Exception:
        return []


def prefetch_all_in_background(on_type_ready: Optional[Callable[[str, List[str]], None]] = None):
    """
    Lanza un hilo por cada tipo para poblar la caché de memoria.
    Solo descarga de la API los tipos cuya caché haya expirado o no exista.
    on_type_ready(server_type, versions) se llama en el hilo worker cuando termina.
    """
    _ensure_table()

    def fetch_one(server_type: str):
        # Primero intentar desde DB (instantáneo si está vigente)
        db_versions = _load_from_db(server_type)
        if db_versions is not None:
            with _memory_lock:
                _memory_cache[server_type] = db_versions
            if on_type_ready:
                on_type_ready(server_type, db_versions)
            return

        # Necesita actualización desde API
        try:
            versions = _fetch_from_api(server_type)
            if versions:
                _save_to_db(server_type, versions)
                with _memory_lock:
                    _memory_cache[server_type] = versions
                if on_type_ready:
                    on_type_ready(server_type, versions)
        except Exception:
            pass

    for stype in SERVER_TYPES:
        threading.Thread(target=fetch_one, args=(stype,), daemon=True).start()


def invalidate(server_type: Optional[str] = None):
    """Fuerza refresco en el próximo acceso. Si server_type es None, borra todo."""
    with _memory_lock:
        if server_type:
            _memory_cache.pop(server_type, None)
        else:
            _memory_cache.clear()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            if server_type:
                conn.execute("DELETE FROM version_cache WHERE server_type = ?", (server_type,))
            else:
                conn.execute("DELETE FROM version_cache")
            conn.commit()
    except Exception:
        pass
