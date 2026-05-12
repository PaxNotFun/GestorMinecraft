import requests

from config.urls import PAPERMC_API_URL
from services import downloader
from .base_installer import BaseInstaller


class PaperInstaller(BaseInstaller):
    def install_server(self, progress_callback):
        """Instala un servidor PaperMC."""
        try:
            builds_url = f"{PAPERMC_API_URL}/versions/{self.sinfo['version']}/builds"
            builds_data = requests.get(
                builds_url,
                headers={'User-Agent': 'GetMineHub'},
                timeout=10
            ).json()

            latest_build = builds_data['builds'][-1]['build']
            jar_name = f"paper-{self.sinfo['version']}-{latest_build}.jar"
            download_url = f"{PAPERMC_API_URL}/versions/{self.sinfo['version']}/builds/{latest_build}/downloads/{jar_name}"

            if not downloader.download_file_with_progress(
                    download_url,
                    self.spath / 'server.jar',
                    progress_callback
            ):
                raise Exception("La descarga del JAR de PaperMC falló.")

            self.sinfo['jar_file'] = 'server.jar'
        except Exception as e:
            raise Exception(f"No se pudo instalar PaperMC: {e}")