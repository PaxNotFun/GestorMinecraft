import requests

from config.urls import VANILLA_API_URL
from services import downloader
from .base_installer import BaseInstaller


class VanillaInstaller(BaseInstaller):
    def install_server(self, progress_callback):
        """Instala un servidor Vanilla de Minecraft."""
        try:
            mc_ver = self.sinfo['version']

            # Obtener el manifest de versiones de Mojang
            manifest = requests.get(
                VANILLA_API_URL,
                headers={'User-Agent': 'GetMineHub'},
                timeout=10
            ).json()

            # Buscar la versión solicitada
            version_entry = next(
                (v for v in manifest['versions'] if v['id'] == mc_ver),
                None
            )

            if not version_entry:
                raise Exception(f"No se encontró la versión Vanilla '{mc_ver}' en el manifest de Mojang.")

            # Obtener el JSON de detalles de esa versión
            version_data = requests.get(
                version_entry['url'],
                headers={'User-Agent': 'GetMineHub'},
                timeout=10
            ).json()

            # Extraer la URL del JAR del servidor
            server_info = version_data.get('downloads', {}).get('server')
            if not server_info or 'url' not in server_info:
                raise Exception(f"No hay JAR de servidor disponible para la versión Vanilla '{mc_ver}'.")

            download_url = server_info['url']

            # Descargar el JAR del servidor
            if not downloader.download_file_with_progress(
                    download_url,
                    self.spath / 'server.jar',
                    progress_callback
            ):
                raise Exception("La descarga del JAR de Vanilla falló.")

            self.sinfo['jar_file'] = 'server.jar'

        except Exception as e:
            raise Exception(f"No se pudo instalar Vanilla: {e}")