from abc import ABC, abstractmethod
from pathlib import Path

import requests

from config.urls import SERVER_PROPERTIES_URL
from services import java_manager
from services.server import server_data
from utils.helpers import check_internet_connection


class BaseInstaller(ABC):
    def __init__(self, sinfo, spath, app_instance, progress_callback,
                 is_reinstall=False, reinstall_mode='partial', is_update=False):
        self.sinfo = sinfo
        self.spath = Path(spath)
        self.app = app_instance
        self.progress_callback = progress_callback
        self.is_reinstall = is_reinstall
        self.reinstall_mode = reinstall_mode
        self.is_update = is_update
        self.temp_backup_path = None

    def _update_progress(self, text=None, progress=None, error=None, success=None, server_data_result=None):
        """Actualiza el progreso en la UI."""
        status = {
            "text": text,
            "progress": progress,
            "error": error,
            "path": str(self.spath),
            "success": success,
            "server_data": server_data_result,
            "reinstall_details": f"reinstall_mode={self.reinstall_mode}",
            "was_reinstall": self.is_reinstall and not self.is_update,
            "was_update": self.is_update
        }
        status = {k: v for k, v in status.items() if v is not None}
        if self.progress_callback:
            self.app.after(0, self.progress_callback, status)

    def run_installation(self):
        """Proceso completo de instalación / reinstalación / actualización."""
        if not check_internet_connection():
            self._update_progress(error="No se puede continuar sin conexión a internet.")
            return

        try:
            if self.is_reinstall or self.is_update:
                verb = "actualización" if self.is_update else "reinstalación"
                self._update_progress(f"Preparando {verb}...", 0.0)

                success, temp_path, msg = server_data.prepare_reinstall(self.spath, self.reinstall_mode)

                if not success:
                    raise Exception(f"Error preparando {verb}: {msg}")

                self.temp_backup_path = temp_path
                self._update_progress(msg, 0.02)

            self._update_progress("Verificando Java...", 0.05)
            mc_ver = self.sinfo['version']
            j_info = java_manager.get_java_info_for_minecraft(mc_ver)
            if not j_info:
                raise Exception(f"No se encontró una versión de Java compatible para MC {mc_ver}.")

            j_exe = java_manager.find_private_java_executable(j_info['java_version'])
            if not j_exe:
                self._update_progress(f"Descargando {j_info['name']}...", 0.10)

                def j_dl_cb(p):
                    self._update_progress(progress=0.10 + (p / 100) * 0.30)

                j_exe = java_manager.download_and_install_java(j_info, j_dl_cb)
                if not j_exe:
                    raise Exception("Java no encontrado incluso después de la instalación.")

            self._update_progress("Java listo.", 0.45)
            self.sinfo['java_executable'] = j_exe

            stype = self.sinfo['type']
            action_verb = "Actualizando" if self.is_update else "Descargando"
            self._update_progress(f"{action_verb} {stype} {mc_ver}...", 0.5)

            def srv_dl_cb(p):
                self._update_progress(progress=0.5 + (p / 100) * 0.4)

            self.install_server(srv_dl_cb)

            self._update_progress("Configurando archivos finales...", 0.98)

            # Solo descargar server.properties si no es reinstalación/update parcial
            if not ((self.is_reinstall or self.is_update) and self.reinstall_mode == 'partial'):
                self._download_server_properties()

            if self.is_reinstall or self.is_update:
                server = server_data.get_server_by_path(str(self.spath))

                if server:
                    updates = {
                        "java_executable": j_exe,
                        "type": self.sinfo['type'],
                        "version": mc_ver,
                        "jar_file": self.sinfo.get('jar_file'),
                        "forge_args_file": self.sinfo.get('forge_args_file'),
                        "forge_launch_type": self.sinfo.get('forge_launch_type')
                    }
                    server_data.update_server(server['uuid'], updates)
                    new_srv_data = server_data.get_server_by_path(str(self.spath))
                else:
                    new_srv_data = {
                        "name": self.sinfo['name'],
                        "path": str(self.spath),
                        "java_executable": j_exe,
                        "type": self.sinfo['type'],
                        "version": mc_ver,
                        "jar_file": self.sinfo.get('jar_file'),
                        "forge_args_file": self.sinfo.get('forge_args_file'),
                        "forge_launch_type": self.sinfo.get('forge_launch_type')
                    }
                    server_data.add_server(new_srv_data)
                    new_srv_data = server_data.get_server_by_path(str(self.spath))

                if self.temp_backup_path:
                    server_data.cleanup_temp_reinstall(self.temp_backup_path)
                    self.temp_backup_path = None

            else:
                local_config = {"min_ram": "2G", "max_ram": "4G", "jvm_args": ""}
                new_srv_data = {
                    "name": self.sinfo['name'],
                    "path": str(self.spath),
                    "java_executable": j_exe,
                    "type": self.sinfo['type'],
                    "version": mc_ver,
                    "jar_file": self.sinfo.get('jar_file'),
                    "forge_args_file": self.sinfo.get('forge_args_file'),
                    "forge_launch_type": self.sinfo.get('forge_launch_type')
                }
                if server_data.add_server(new_srv_data):
                    server = server_data.get_server_by_path(str(self.spath))
                    if server:
                        server_data.save_server_config(self.spath, local_config)
                        new_srv_data = server
                else:
                    raise Exception("Error al guardar el servidor en la base de datos")

            self._update_progress(text="¡Completado!", progress=1.0, success=True, server_data_result=new_srv_data)

        except Exception as e:
            # Rollback garantizado si hay backup temporal (update, reinstall parcial o total)
            if self.temp_backup_path:
                verb = "actualización" if self.is_update else "reinstalación"
                self._update_progress(
                    f"Error en {verb}, restaurando archivos originales...", 0.99
                )
                restore_success = server_data.restore_from_temp_reinstall(
                    self.spath, self.temp_backup_path
                )
                if restore_success:
                    error_msg = (
                        f"{str(e)}\n\n"
                        "✅ Rollback completado: tus archivos originales han sido restaurados."
                    )
                else:
                    error_msg = (
                        f"{str(e)}\n\n"
                        "⚠️ ADVERTENCIA: No se pudieron restaurar completamente los archivos originales.\n"
                        f"Revisa manualmente la carpeta del servidor."
                    )
                self._update_progress(error=error_msg)
            else:
                self._update_progress(error=str(e))

    def _download_server_properties(self):
        """Descarga el archivo server.properties."""
        try:
            response = requests.get(
                SERVER_PROPERTIES_URL,
                headers={'User-Agent': 'GetMineHub'},
                timeout=10
            )
            response.raise_for_status()
            (self.spath / 'server.properties').write_text(response.text, encoding='utf-8')
        except requests.exceptions.RequestException:
            (self.spath / 'server.properties').write_text("", encoding='utf-8')

    @abstractmethod
    def install_server(self, progress_callback):
        pass
