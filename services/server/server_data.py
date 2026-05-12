"""
Gestión de datos de servidores usando SQLite
VERSIÓN MEJORADA: Detección inteligente de mundos + Sin importación/exportación
"""

import json
import shutil
import uuid
from pathlib import Path
from tkinter import messagebox
from typing import Dict, List, Optional, Tuple

from config.general import APP_DIR, get_servers_base_dir
from services.server.server_database import (
    ServerDatabase,
    migrate_from_json_to_sqlite,
    DB_PATH
)

from config.general import SERVERS_FILE_PATH


def ensure_database_initialized():
    """Asegura que la base de datos esté inicializada y migrada si es necesario."""
    # Solo migrar si existe el JSON y NO existe la base de datos
    if SERVERS_FILE_PATH.exists() and not DB_PATH.exists():
        migrate_from_json_to_sqlite(SERVERS_FILE_PATH)
    elif not DB_PATH.exists():
        # Si no hay JSON ni DB, solo crear la DB
        ServerDatabase()


def load_servers() -> List[Dict]:
    """Carga todos los servidores desde la base de datos."""
    ensure_database_initialized()
    db = ServerDatabase()
    return db.get_all_servers()


def save_servers(servers_list: List[Dict]) -> bool:
    """Función de compatibilidad. Con SQLite no necesitas guardar manualmente."""
    return True


def get_server_by_path(path: str) -> Optional[Dict]:
    """Obtiene un servidor por su path."""
    db = ServerDatabase()
    return db.get_server_by_path(str(path))


def get_server_by_uuid(server_uuid: str) -> Optional[Dict]:
    """Obtiene un servidor por su UUID."""
    db = ServerDatabase()
    return db.get_server_by_uuid(server_uuid)


def add_server(server_data: Dict) -> bool:
    """Añade un nuevo servidor a la base de datos."""
    if 'uuid' not in server_data:
        server_data['uuid'] = str(uuid.uuid4())
    
    db = ServerDatabase()
    return db.add_server(server_data)


def update_server(server_uuid: str, updates: Dict) -> bool:
    """Actualiza la información de un servidor."""
    db = ServerDatabase()
    return db.update_server(server_uuid, updates)


def update_server_by_path(path: str, updates: Dict) -> bool:
    """Actualiza un servidor usando su path."""
    server = get_server_by_path(path)
    if not server:
        return False
    return update_server(server['uuid'], updates)


def delete_server(server_info: Dict, delete_files: bool = True) -> Tuple[bool, str]:
    """
    Elimina un servidor de la base de datos y opcionalmente sus archivos.
    
    Args:
        server_info: Diccionario con información del servidor
        delete_files: Si True, elimina también los archivos del servidor
    
    Returns:
        (success, message)
    """
    try:
        server_path = Path(server_info['path'])
        server_uuid = server_info.get('uuid')
        
        if not server_uuid:
            server = get_server_by_path(str(server_path))
            if server:
                server_uuid = server['uuid']
            else:
                return False, "No se pudo encontrar el servidor en la base de datos."
        
        db = ServerDatabase()
        if not db.delete_server(server_uuid):
            return False, "Error al eliminar el servidor de la base de datos."
        
        if delete_files and server_path.exists():
            try:
                shutil.rmtree(server_path)
                message = f"Servidor '{server_info['name']}' eliminado completamente."
            except Exception as e:
                message = f"Servidor eliminado de la lista, pero hubo un error al eliminar archivos: {e}"
        else:
            message = f"Servidor '{server_info['name']}' eliminado de la lista."
        
        return True, message
        
    except Exception as e:
        return False, f"Error al eliminar servidor: {e}"


def generate_server_folder_name() -> str:
    """Genera un nombre único de carpeta basado en UUID."""
    return str(uuid.uuid4())


def load_server_config(server_path: Path) -> Dict:
    """Carga la configuración local de un servidor."""
    server = get_server_by_path(str(server_path))
    
    if server:
        return {
            'min_ram': server.get('min_ram', '2G'),
            'max_ram': server.get('max_ram', '4G'),
            'jvm_args': server.get('jvm_args', ''),
            'use_aikar_flags': bool(server.get('use_aikar_flags', 0))
        }
    
    return {
        'min_ram': '2G',
        'max_ram': '4G',
        'jvm_args': '',
        'use_aikar_flags': False
    }


def save_server_config(server_path: Path, config: Dict) -> bool:
    """Guarda la configuración local de un servidor."""
    server = get_server_by_path(str(server_path))
    
    if not server:
        return False
    
    db = ServerDatabase()
    return db.update_server_config(server['uuid'], config)


def accept_eula(server_path: Path) -> bool:
    """
    Acepta automáticamente el EULA de Minecraft.
    
    Args:
        server_path: Ruta del servidor
    
    Returns:
        True si se aceptó correctamente
    """
    try:
        eula_path = Path(server_path) / 'eula.txt'
        eula_path.write_text('eula=true', encoding='utf-8')
        return True
    except Exception:
        return False


def detect_minecraft_worlds(server_path: Path) -> List[str]:
    """
    Detecta TODOS los mundos de Minecraft en el servidor de forma inteligente.
    Busca carpetas que contengan level.dat, level.dat_old o session.lock
    
    Args:
        server_path: Ruta del servidor
    
    Returns:
        Lista de nombres de carpetas que son mundos válidos
    """
    worlds = []
    
    try:
        for item in server_path.iterdir():
            if item.is_dir():
                level_dat = item / 'level.dat'
                level_dat_old = item / 'level.dat_old'
                session_lock = item / 'session.lock'
                
                has_world_file = (
                    (level_dat.exists() and level_dat.is_file()) or
                    (level_dat_old.exists() and level_dat_old.is_file()) or
                    (session_lock.exists() and session_lock.is_file())
                )
                
                if has_world_file:
                    worlds.append(item.name)
    
    except Exception:
        pass
    
    return worlds


def get_items_to_preserve(server_path: Path, reinstall_mode: str) -> Tuple[List[str], List[str], List[str], List[str]]:
    """
    Obtiene dinámicamente los items a preservar según el modo de reinstalación.
    Busca solo en la carpeta raíz del servidor.
    
    Args:
        server_path: Ruta del servidor
        reinstall_mode: 'partial' o 'total'
    
    Returns:
        Lista de nombres de items a conservar
    """
    if reinstall_mode == 'total':
        return []
    
    items_to_keep = []
    
    important_folders = [
        'plugins',
        'mods', 
        'config',
        'versions'
    ]
    
    important_files = [
        'server.properties',
        'eula.txt',
        'ops.json',
        'whitelist.json',
        'banned-players.json',
        'banned-ips.json',
        'permissions.yml',
        'bukkit.yml',
        'spigot.yml',
        'paper.yml',
        'server-icon.png',
        'user_cache.json',
        'usernamecache.json'
    ]
    
    detected_worlds = []
    detected_folders = []
    detected_files = []
    
    try:
        for item in server_path.iterdir():
            try:
                if not item.exists():
                    continue
                    
                item_name = item.name
                
                if item.is_dir():
                    level_dat = item / 'level.dat'
                    level_dat_old = item / 'level.dat_old'
                    session_lock = item / 'session.lock'
                    
                    has_world_file = (
                        (level_dat.exists() and level_dat.is_file()) or
                        (level_dat_old.exists() and level_dat_old.is_file()) or
                        (session_lock.exists() and session_lock.is_file())
                    )
                    
                    if has_world_file:
                        items_to_keep.append(item_name)
                        detected_worlds.append(item_name)
                        continue
                    
                    if item_name in important_folders:
                        items_to_keep.append(item_name)
                        detected_folders.append(item_name)
                        continue
                
                if item.is_file() and item_name in important_files:
                    items_to_keep.append(item_name)
                    detected_files.append(item_name)
                    
            except Exception:
                continue
    
    except Exception:
        pass
    
    return list(dict.fromkeys(items_to_keep)), detected_worlds, detected_folders, detected_files


def prepare_reinstall(server_path: Path, reinstall_mode: str) -> Tuple[bool, Optional[Path], str]:
    """
    Prepara el servidor para reinstalación según el modo.
    VERSIÓN MEJORADA con detección inteligente de mundos.
    
    Args:
        server_path: Ruta del servidor
        reinstall_mode: 'partial' o 'total'
    
    Returns:
        (success, temp_backup_path, message)
    """
    try:
        server_path = Path(server_path)
        
        if not server_path.exists():
            return False, None, "La ruta del servidor no existe."
        
        temp_backup = server_path.parent / f".temp_reinstall_{server_path.name}"
        
        if temp_backup.exists():
            shutil.rmtree(temp_backup)
        
        temp_backup.mkdir()
        
        if reinstall_mode == 'partial':
            items_to_keep, detected_worlds, detected_folders, detected_files = get_items_to_preserve(server_path, reinstall_mode)
            
            if not items_to_keep:
                return False, None, "No se detectaron items para conservar."
            
            msg_parts = ["Se conservarán los siguientes elementos:\n"]
            
            if detected_worlds:
                msg_parts.append(f"\n🌍 Mundos ({len(detected_worlds)}):")
                for world in detected_worlds:
                    msg_parts.append(f"  • {world}")
            
            if detected_folders:
                msg_parts.append(f"\n📁 Carpetas ({len(detected_folders)}):")
                for folder in detected_folders:
                    msg_parts.append(f"  • {folder}")
            
            if detected_files:
                msg_parts.append(f"\n📄 Archivos ({len(detected_files)}):")
                for file in detected_files:
                    msg_parts.append(f"  • {file}")
            
            msg_parts.append(f"\n\nTOTAL: {len(items_to_keep)} elementos")
            msg_parts.append("\n¿Desea continuar con la reinstalación?")
            
            confirm = messagebox.askyesno(
                "Confirmar Elementos a Conservar",
                "\n".join(msg_parts)
            )
            
            if not confirm:
                return False, None, "Reinstalación cancelada por el usuario."
            
            backed_up_items = []
            failed_items = []
            
            for item_name in items_to_keep:
                item_path = server_path / item_name
                if item_path.exists():
                    dest = temp_backup / item_name
                    try:
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        
                        if item_path.is_dir():
                            shutil.copytree(item_path, dest)
                        else:
                            shutil.copy2(item_path, dest)
                        backed_up_items.append(item_name)
                    except Exception as e:
                        failed_items.append(f"{item_name} ({str(e)})")
            
            if failed_items:
                error_msg = f"Error al copiar los siguientes elementos:\n" + "\n".join(failed_items)
                return False, None, error_msg
            
            for item in server_path.iterdir():
                if item.name not in backed_up_items:
                    try:
                        if item.is_dir():
                            shutil.rmtree(item, ignore_errors=True)
                        else:
                            item.unlink(missing_ok=True)
                    except Exception:
                        pass
            
            worlds_backed_up = [w for w in backed_up_items if w in detected_worlds]
            
            message = f"Respaldados {len(backed_up_items)} items ({len(worlds_backed_up)} mundos detectados)"
            
        else:  # total
            local_config = load_server_config(server_path)
            config_file = temp_backup / 'local_config.json'
            config_file.write_text(json.dumps(local_config), encoding='utf-8')
            
            shutil.rmtree(server_path)
            server_path.mkdir()
            
            message = "Preparando reinstalación total (limpieza completa)..."
        
        return True, temp_backup, message
        
    except Exception as e:
        return False, None, f"Error preparando reinstalación: {str(e)}"


def restore_from_temp_reinstall(server_path: Path, temp_backup_path: Path) -> bool:
    """Restaura los archivos desde el backup temporal en caso de error."""
    try:
        if not temp_backup_path or not temp_backup_path.exists():
            return False
        
        server_path = Path(server_path)
        
        for item in temp_backup_path.iterdir():
            dest = server_path / item.name
            
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)
        
        shutil.rmtree(temp_backup_path, ignore_errors=True)
        
        return True
        
    except Exception:
        return False


def cleanup_temp_reinstall(temp_backup_path: Path) -> bool:
    """Limpia el backup temporal después de una reinstalación exitosa."""
    try:
        if temp_backup_path and temp_backup_path.exists():
            shutil.rmtree(temp_backup_path, ignore_errors=True)
        return True
    except Exception:
        return False


def get_database_stats() -> Dict:
    """Obtiene estadísticas de la base de datos."""
    servers = load_servers()
    
    stats = {
        'total_servers': len(servers),
        'by_type': {},
        'by_version': {},
        'database_path': str(DB_PATH),
        'database_size_mb': round(DB_PATH.stat().st_size / (1024 * 1024), 2) if DB_PATH.exists() else 0
    }
    
    for server in servers:
        server_type = server.get('type', 'Unknown')
        stats['by_type'][server_type] = stats['by_type'].get(server_type, 0) + 1
        
        version = server.get('version', 'Unknown')
        stats['by_version'][version] = stats['by_version'].get(version, 0) + 1
    
    return stats
