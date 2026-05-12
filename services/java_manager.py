import os
import re
import subprocess
import sys
import tempfile

from packaging import version

from config.defaults import JAVA_MAPPING
from config.general import JAVA_RUNTIMES_DIR
from services import downloader

# Nombre del ejecutable de Java según plataforma
JAVA_EXECUTABLE_NAME = 'java.exe' if sys.platform == 'win32' else 'java'


def get_java_info_for_minecraft(minecraft_version_str):
    """Obtiene la información de Java requerida para una versión de Minecraft."""
    try:
        mc_ver = version.parse(minecraft_version_str)
        for req in JAVA_MAPPING:
            if mc_ver >= version.parse(req['mc_version']):
                return req
    except version.InvalidVersion:
        return None
    return None


def find_private_java_executable(required_major_version):
    """Busca una versión específica de Java en el directorio de runtimes privados."""
    if not JAVA_RUNTIMES_DIR.exists():
        return None

    for item_name in os.listdir(JAVA_RUNTIMES_DIR):
        item_path = JAVA_RUNTIMES_DIR / item_name
        if item_path.is_dir():
            java_exe = item_path / 'bin' / JAVA_EXECUTABLE_NAME
            if java_exe.exists():
                try:
                    startupinfo = None
                    if sys.platform == "win32":
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                    output = subprocess.check_output(
                        [str(java_exe), '-version'],
                        stderr=subprocess.STDOUT,
                        text=True,
                        encoding='utf-8',
                        startupinfo=startupinfo
                    )

                    first_line = output.splitlines()[0]
                    match = re.search(r'version "(\d+)', first_line)
                    if match:
                        major_version = int(match.group(1))
                        if major_version == required_major_version:
                            return str(java_exe)
                        # Manejar formato antiguo "1.8"
                        elif major_version == 1 and required_major_version < 9:
                            match_old = re.search(r'version "1\.(\d+)', first_line)
                            if match_old and int(match_old.group(1)) == required_major_version:
                                return str(java_exe)

                except (subprocess.CalledProcessError, FileNotFoundError, IndexError):
                    continue
    return None


def download_and_install_java(j_info, progress_callback):
    """Descarga y extrae una versión de Java."""
    with tempfile.TemporaryDirectory() as temp_dir:
        archive_name = os.path.basename(j_info['url'])
        archive_path = os.path.join(temp_dir, archive_name)

        if not downloader.download_file_with_progress(j_info['url'], archive_path, progress_callback):
            raise Exception(f"Fallo al descargar {j_info['name']}.")

        if not downloader.extract_archive(archive_path, JAVA_RUNTIMES_DIR):
            raise Exception("Fallo al extraer el archivo de Java.")

    java_exe = find_private_java_executable(j_info['java_version'])

    # En Linux/macOS los binarios extraídos del .tar.gz pueden no tener
    # permisos de ejecución; los asignamos explícitamente.
    if java_exe and sys.platform != 'win32':
        try:
            os.chmod(java_exe, 0o755)
            # Asegurar también el directorio bin completo
            bin_dir = os.path.dirname(java_exe)
            for bin_file in os.listdir(bin_dir):
                bin_path = os.path.join(bin_dir, bin_file)
                if os.path.isfile(bin_path):
                    os.chmod(bin_path, 0o755)
        except OSError:
            pass

    return java_exe


def get_available_java_runtimes():
    """Escanea el directorio de runtimes y devuelve una lista de Javas disponibles."""
    runtimes = []
    if not JAVA_RUNTIMES_DIR.exists():
        return runtimes

    for item_name in os.listdir(JAVA_RUNTIMES_DIR):
        item_path = JAVA_RUNTIMES_DIR / item_name
        if item_path.is_dir():
            java_exe = item_path / 'bin' / JAVA_EXECUTABLE_NAME
            if java_exe.exists():
                try:
                    startupinfo = None
                    if sys.platform == "win32":
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                    output = subprocess.check_output(
                        [str(java_exe), '-version'],
                        stderr=subprocess.STDOUT,
                        text=True,
                        encoding='utf-8',
                        startupinfo=startupinfo
                    )
                    first_line = output.splitlines()[0]

                    version_match = re.search(r'version "(\d+(\.\d+)*)', first_line)
                    name_match = re.search(r'(OpenJDK|Temurin).*?version', output, re.IGNORECASE)

                    if version_match:
                        version_str = version_match.group(1)
                        major_version = int(version_str.split('.')[0])
                        if major_version == 1:  # Formato antiguo 1.8
                            major_version = int(version_str.split('.')[1])

                        runtime_info = {
                            "name": name_match.group(1).strip() if name_match else f"Java {major_version}",
                            "version": major_version,
                            "path": str(java_exe)
                        }
                        runtimes.append(runtime_info)

                except (subprocess.CalledProcessError, FileNotFoundError, IndexError):
                    continue

    return sorted(runtimes, key=lambda x: x['version'], reverse=True)