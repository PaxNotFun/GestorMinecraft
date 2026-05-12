"""
Sistema de Almacenamiento con SQLite para GetMineHub
Migración automática desde JSON sin backups
"""

import json
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from config.general import APP_DIR


DB_PATH = APP_DIR / "servers.db"


class ServerDatabase:
    """Gestor de base de datos SQLite para servidores."""
    
    def __init__(self):
        self.db_path = DB_PATH
        self._init_database()
    
    def _init_database(self):
        """Inicializa la base de datos y crea tablas si no existen."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS servers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    path TEXT UNIQUE NOT NULL,
                    type TEXT NOT NULL,
                    version TEXT NOT NULL,
                    java_executable TEXT,
                    jar_file TEXT,
                    forge_args_file TEXT,
                    forge_launch_type TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS server_config (
                    server_uuid TEXT PRIMARY KEY,
                    min_ram TEXT DEFAULT '2G',
                    max_ram TEXT DEFAULT '4G',
                    jvm_args TEXT DEFAULT '',
                    use_aikar_flags INTEGER DEFAULT 0,
                    FOREIGN KEY (server_uuid) REFERENCES servers(uuid) ON DELETE CASCADE
                )
            """)

            # Migración: añadir columna si ya existía la tabla sin ella
            try:
                conn.execute("ALTER TABLE server_config ADD COLUMN use_aikar_flags INTEGER DEFAULT 0")
                conn.commit()
            except Exception:
                pass  # La columna ya existe
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_server_uuid ON servers(uuid)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_server_name ON servers(name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_server_type ON servers(type)")
            
            conn.commit()
    
    def add_server(self, server_data: Dict) -> bool:
        """Añade un nuevo servidor a la base de datos."""
        try:
            server_uuid = server_data.get('uuid', str(uuid.uuid4()))
            now = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO servers (
                        uuid, name, path, type, version,
                        java_executable, jar_file, forge_args_file, forge_launch_type,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    server_uuid,
                    server_data['name'],
                    server_data['path'],
                    server_data['type'],
                    server_data['version'],
                    server_data.get('java_executable'),
                    server_data.get('jar_file'),
                    server_data.get('forge_args_file'),
                    server_data.get('forge_launch_type'),
                    now,
                    now
                ))
                
                conn.execute("""
                    INSERT INTO server_config (server_uuid, min_ram, max_ram, jvm_args)
                    VALUES (?, ?, ?, ?)
                """, (server_uuid, '2G', '4G', ''))
                
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        except Exception:
            return False
    
    def get_server_by_path(self, path: str) -> Optional[Dict]:
        """Obtiene un servidor por su path."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT s.*, c.min_ram, c.max_ram, c.jvm_args, c.use_aikar_flags
                FROM servers s
                LEFT JOIN server_config c ON s.uuid = c.server_uuid
                WHERE s.path = ?
            """, (path,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_server_by_uuid(self, server_uuid: str) -> Optional[Dict]:
        """Obtiene un servidor por su UUID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT s.*, c.min_ram, c.max_ram, c.jvm_args, c.use_aikar_flags
                FROM servers s
                LEFT JOIN server_config c ON s.uuid = c.server_uuid
                WHERE s.uuid = ?
            """, (server_uuid,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_servers(self) -> List[Dict]:
        """Obtiene todos los servidores."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT s.*, c.min_ram, c.max_ram, c.jvm_args, c.use_aikar_flags
                FROM servers s
                LEFT JOIN server_config c ON s.uuid = c.server_uuid
                ORDER BY s.name
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def update_server(self, server_uuid: str, updates: Dict) -> bool:
        """Actualiza un servidor."""
        try:
            allowed_fields = [
                'name', 'type', 'version', 'java_executable',
                'jar_file', 'forge_args_file', 'forge_launch_type'
            ]
            
            filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
            
            if not filtered_updates:
                return False
            
            set_clause = ", ".join([f"{k} = ?" for k in filtered_updates.keys()])
            values = list(filtered_updates.values())
            values.append(datetime.now().isoformat())
            values.append(server_uuid)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(f"""
                    UPDATE servers
                    SET {set_clause}, updated_at = ?
                    WHERE uuid = ?
                """, values)
                conn.commit()
            
            return True
        except Exception:
            return False
    
    def update_server_config(self, server_uuid: str, config: Dict) -> bool:
        """Actualiza la configuración de un servidor."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO server_config (server_uuid, min_ram, max_ram, jvm_args, use_aikar_flags)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    server_uuid,
                    config.get('min_ram', '2G'),
                    config.get('max_ram', '4G'),
                    config.get('jvm_args', ''),
                    1 if config.get('use_aikar_flags', False) else 0
                ))
                conn.commit()
            return True
        except Exception:
            return False
    
    def delete_server(self, server_uuid: str) -> bool:
        """Elimina un servidor de la base de datos."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM servers WHERE uuid = ?", (server_uuid,))
                conn.commit()
            return True
        except Exception:
            return False
    
    def search_servers(self, query: str) -> List[Dict]:
        """Busca servidores por nombre o tipo."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT s.*, c.min_ram, c.max_ram, c.jvm_args, c.use_aikar_flags
                FROM servers s
                LEFT JOIN server_config c ON s.uuid = c.server_uuid
                WHERE s.name LIKE ? OR s.type LIKE ?
                ORDER BY s.name
            """, (f"%{query}%", f"%{query}%"))
            return [dict(row) for row in cursor.fetchall()]


def migrate_from_json_to_sqlite(json_path: Path) -> bool:
    """Migra servidores desde el sistema JSON antiguo a SQLite sin crear backups."""
    try:
        if not json_path.exists():
            return True
        
        # Leer datos del JSON
        data = json.loads(json_path.read_text(encoding='utf-8'))
        
        if not data:  # Si el JSON está vacío, solo eliminarlo
            json_path.unlink()
            return True
        
        # Crear base de datos e importar
        db = ServerDatabase()
        
        imported = 0
        errors = 0
        
        for server in data:
            try:
                required = ['name', 'path', 'type', 'version']
                if not all(field in server for field in required):
                    errors += 1
                    continue
                
                if db.add_server(server):
                    if 'config' in server:
                        server_uuid = server.get('uuid')
                        if not server_uuid:
                            created_server = db.get_server_by_path(server['path'])
                            if created_server:
                                server_uuid = created_server['uuid']
                        
                        if server_uuid:
                            db.update_server_config(server_uuid, server['config'])
                    imported += 1
                else:
                    errors += 1
                    
            except Exception:
                errors += 1
        
        # Eliminar archivo JSON antiguo sin crear backup
        json_path.unlink()
        
        return True
        
    except Exception:
        return False


# Funciones de compatibilidad
def load_servers() -> List[Dict]:
    """Carga todos los servidores."""
    db = ServerDatabase()
    return db.get_all_servers()


def save_servers(servers_list: List[Dict]) -> bool:
    """Compatibilidad - SQLite persiste automáticamente."""
    return True


def get_server_by_path(path: str) -> Optional[Dict]:
    """Obtiene un servidor por path."""
    db = ServerDatabase()
    return db.get_server_by_path(path)


def add_server(server_data: Dict) -> bool:
    """Añade un servidor."""
    db = ServerDatabase()
    return db.add_server(server_data)


def update_server(server_uuid: str, updates: Dict) -> bool:
    """Actualiza un servidor."""
    db = ServerDatabase()
    return db.update_server(server_uuid, updates)


def delete_server_by_uuid(server_uuid: str) -> bool:
    """Elimina un servidor."""
    db = ServerDatabase()
    return db.delete_server(server_uuid)
