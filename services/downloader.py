import tarfile
import zipfile
from pathlib import Path

import requests

from config.defaults import DEFAULT_TIMEOUT
from config.general import load_setting


def download_file_with_progress(url, destination_path, progress_callback=lambda p: None):
    """Descarga un archivo y reporta el progreso."""
    try:
        dest_path_obj = Path(destination_path)
        dest_path_obj.parent.mkdir(parents=True, exist_ok=True)

        response = requests.get(
            url,
            stream=True,
            headers={'User-Agent': 'GetMineHub'},
            timeout=load_setting("timeout", DEFAULT_TIMEOUT)
        )
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))

        with open(dest_path_obj, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    progress = (downloaded / total_size) * 100
                    if progress_callback:
                        progress_callback(progress)

        if progress_callback:
            progress_callback(100)
        return True
    except requests.exceptions.RequestException:
        return False
    except IOError:
        return False


def extract_zip(zip_path, destination_dir):
    """Extrae un archivo ZIP de forma segura."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(destination_dir)
        return True
    except (zipfile.BadZipFile, OSError):
        return False


def extract_targz(tar_path, destination_dir):
    """Extrae un archivo .tar.gz de forma segura (usado en Linux/macOS)."""
    try:
        with tarfile.open(tar_path, 'r:gz') as tar_ref:
            tar_ref.extractall(destination_dir)
        return True
    except (tarfile.TarError, OSError):
        return False


def extract_archive(archive_path, destination_dir):
    """Extrae un archivo comprimido detectando su formato automáticamente (.zip o .tar.gz)."""
    archive_path = str(archive_path)
    if archive_path.endswith('.tar.gz') or archive_path.endswith('.tgz'):
        return extract_targz(archive_path, destination_dir)
    else:
        return extract_zip(archive_path, destination_dir)