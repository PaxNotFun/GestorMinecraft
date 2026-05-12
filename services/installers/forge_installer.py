import re
import subprocess
import sys
from pathlib import Path

import requests

from config.urls import FORGE_API_URL, FORGE_MAVEN_URL
from services import downloader
from .base_installer import BaseInstaller


class ForgeInstaller(BaseInstaller):
    def install_server(self, progress_callback):
        """Instala un servidor Forge con detección del tipo de lanzamiento."""
        try:
            promos = requests.get(
                FORGE_API_URL,
                headers={'User-Agent': 'GetMineHub'},
                timeout=10
            ).json().get('promos', {})

            mc_ver = self.sinfo['version']
            version_key = f"{mc_ver}-recommended"
            if version_key not in promos:
                version_key = f"{mc_ver}-latest"
            if version_key not in promos:
                raise Exception(f"No se encontró versión para Forge en MC {mc_ver}.")

            forge_ver_part = promos[version_key]
            full_forge_ver = f"{mc_ver}-{forge_ver_part}"

            # Descargar instalador
            installer_url = f"{FORGE_MAVEN_URL}{full_forge_ver}/forge-{full_forge_ver}-installer.jar"
            inst_path = self.spath / 'installer.jar'

            if not downloader.download_file_with_progress(installer_url, inst_path, progress_callback):
                raise Exception("La descarga del instalador de Forge falló.")

            # Ejecutar instalador
            self._update_progress("Instalando Forge...", 0.92)
            startupinfo = subprocess.STARTUPINFO() if sys.platform == "win32" else None
            if startupinfo:
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            proc = subprocess.run(
                [self.sinfo['java_executable'], '-jar', str(inst_path), '--installServer'],
                cwd=str(self.spath),
                capture_output=True,
                text=True,
                check=False,
                startupinfo=startupinfo
            )

            if proc.returncode != 0:
                raise Exception(f"Instalador de Forge falló:\n{proc.stderr}")

            # DETECCIÓN ROBUSTA DEL TIPO DE LANZAMIENTO
            launch_type = self._detect_forge_launch_type(mc_ver, forge_ver_part)

            if launch_type == "modern":
                self._setup_modern_forge(forge_ver_part)
            else:
                self._setup_legacy_forge(mc_ver)

        except Exception as e:
            raise Exception(f"No se pudo instalar Forge: {e}")

    def _detect_forge_launch_type(self, mc_version, forge_version):
        """
        Detecta el tipo de lanzamiento de Forge basándose en múltiples criterios.
        Returns: "modern" o "legacy"
        """
        from packaging import version

        try:
            mc_ver_parsed = version.parse(mc_version)
            if mc_ver_parsed >= version.parse("1.17.0"):
                return "modern"
            elif mc_ver_parsed < version.parse("1.17.0"):
                return "legacy"
        except:
            pass

        args_filename = "win_args.txt" if sys.platform == "win32" else "unix_args.txt"

        forge_libs_path = self.spath / 'libraries' / 'net' / 'minecraftforge' / 'forge'

        if forge_libs_path.exists():
            args_files = list(forge_libs_path.rglob(args_filename))

            if args_files:
                return "modern"

        run_script = self.spath / ('run.bat' if sys.platform == "win32" else 'run.sh')
        if run_script.exists():
            return "modern"

        forge_jar_pattern = re.compile(rf"forge-.*{re.escape(mc_version)}-.*\.jar$", re.IGNORECASE)
        for f in self.spath.glob('*.jar'):
            if forge_jar_pattern.search(f.name):
                return "legacy"

        return "legacy"

    def _setup_modern_forge(self, forge_version):
        """Configura Forge moderno (1.17+) con sistema de argumentos."""
        args_filename = "win_args.txt" if sys.platform == "win32" else "unix_args.txt"
        forge_libs_path = self.spath / 'libraries' / 'net' / 'minecraftforge' / 'forge'

        args_file_path = None

        if forge_libs_path.exists():
            # Buscar el archivo de argumentos
            found_files = list(forge_libs_path.rglob(args_filename))

            if found_files:
                # Priorizar el que contiene la versión exacta
                best_match = None
                for f_path in found_files:
                    if forge_version in str(f_path):
                        best_match = f_path
                        break

                args_file_path = best_match if best_match else found_files[0]

        if not args_file_path or not args_file_path.exists():
            raise Exception(
                "Forge moderno detectado pero no se encontró el archivo de argumentos. "
                "La instalación puede estar corrupta."
            )

        # Guardar la configuración para Forge moderno
        self.sinfo['forge_launch_type'] = 'modern'
        self.sinfo['forge_args_file'] = str(args_file_path.relative_to(self.spath)).replace('\\', '/')

        # Para Forge moderno, NO usamos jar_file tradicional
        # El lanzamiento se hace a través de los archivos de argumentos
        self.sinfo['jar_file'] = None

        self._update_progress("Forge moderno configurado correctamente.", 0.98)

    def _setup_legacy_forge(self, mc_version):
        """Configura Forge legacy (<=1.16.5) con JAR único."""
        server_jar_found = None
        forge_jar_pattern = re.compile(rf"forge-.*{re.escape(mc_version)}-.*\.jar$", re.IGNORECASE)

        # Buscar el JAR de Forge
        for f in self.spath.glob('*.jar'):
            if forge_jar_pattern.search(f.name):
                # Priorizar el que contiene "universal"
                if "universal" in f.name.lower():
                    server_jar_found = f
                    break
                if not server_jar_found:
                    server_jar_found = f

        if not server_jar_found:
            raise Exception(
                "Forge legacy detectado pero no se encontró el JAR del servidor. "
                "La instalación puede haber fallado."
            )

        # Renombrar a server.jar para consistencia
        target_jar = self.spath / 'server.jar'
        if server_jar_found.resolve() != target_jar.resolve():
            if target_jar.exists():
                target_jar.unlink()
            server_jar_found.rename(target_jar)

        # Guardar la configuración para Forge legacy
        self.sinfo['forge_launch_type'] = 'legacy'
        self.sinfo['jar_file'] = 'server.jar'
        self.sinfo['forge_args_file'] = None

        self._update_progress("Forge legacy configurado correctamente.", 0.98)