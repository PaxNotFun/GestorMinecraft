import subprocess
import sys

import requests

from config.urls import FABRIC_META_URL, FABRIC_MAVEN_URL
from services import downloader
from .base_installer import BaseInstaller


class FabricInstaller(BaseInstaller):
    def install_server(self, progress_callback):
        """Instala un servidor Fabric."""
        try:
            mc_ver = self.sinfo['version']
            j_exe = self.sinfo['java_executable']

            # Obtener versiones
            installer_versions = requests.get(
                f"{FABRIC_META_URL}/versions/installer",
                headers={'User-Agent': 'GetMineHub'},
                timeout=10
            ).json()

            loader_versions = requests.get(
                f"{FABRIC_META_URL}/versions/loader/{mc_ver}",
                headers={'User-Agent': 'GetMineHub'},
                timeout=10
            ).json()

            latest_installer = installer_versions[0]['version']
            latest_loader = loader_versions[0]['loader']['version']

            # Descargar instalador
            installer_url = f"{FABRIC_MAVEN_URL}{latest_installer}/fabric-installer-{latest_installer}.jar"
            installer_path = self.spath / 'fabric-installer.jar'

            if not downloader.download_file_with_progress(
                    installer_url,
                    installer_path,
                    lambda p: progress_callback(p * 0.5)
            ):
                raise Exception("La descarga del instalador de Fabric falló.")

            # Ejecutar instalador
            self._update_progress("Instalando Fabric...", 0.75)
            command = [
                j_exe, '-jar', str(installer_path),
                'server', '-mcversion', mc_ver,
                '-loader', latest_loader,
                '-downloadMinecraft'
            ]

            startupinfo = subprocess.STARTUPINFO() if sys.platform == "win32" else None
            if startupinfo:
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            proc = subprocess.run(
                command,
                cwd=str(self.spath),
                capture_output=True,
                text=True,
                check=False,
                startupinfo=startupinfo,
                encoding='utf-8',
                errors='replace'
            )

            if proc.returncode != 0:
                raise Exception(f"El instalador de Fabric falló:\n{proc.stdout}\n{proc.stderr}")

            # Verificar launcher
            fabric_launcher_filename = 'fabric-server-launch.jar'
            fabric_launcher_path = self.spath / fabric_launcher_filename

            if fabric_launcher_path.exists():
                self.sinfo['jar_file'] = fabric_launcher_filename
            else:
                raise Exception("No se encontró 'fabric-server-launch.jar' después de la instalación.")
        except Exception as e:
            raise Exception(f"No se pudo instalar Fabric: {e}")