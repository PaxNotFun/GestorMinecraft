# Valores por defecto
import sys

DEFAULT_TIMEOUT = 15  # Timeout en segundos para peticiones de red
DEFAULT_MIN_RAM = "1G"
DEFAULT_MAX_RAM = "2G"
DEFAULT_JVM_ARGS = ""

# Java version mapping — urls separadas por plataforma
# En Linux se descarga .tar.gz; en Windows se descarga .zip
_JAVA_MAPPING_ALL = [
    {
        'mc_version': '1.20.5',
        'java_version': 21,
        'url_windows': 'https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.4%2B7/OpenJDK21U-jdk_x64_windows_hotspot_21.0.4_7.zip',
        'url_linux':   'https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.4%2B7/OpenJDK21U-jdk_x64_linux_hotspot_21.0.4_7.tar.gz',
        'name': 'Temurin JDK 21'
    },
    {
        'mc_version': '1.17.1',
        'java_version': 17,
        'url_windows': 'https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.12%2B7/OpenJDK17U-jdk_x64_windows_hotspot_17.0.12_7.zip',
        'url_linux':   'https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.12%2B7/OpenJDK17U-jdk_x64_linux_hotspot_17.0.12_7.tar.gz',
        'name': 'Temurin JDK 17'
    },
    {
        'mc_version': '1.17.0',
        'java_version': 16,
        'url_windows': 'https://github.com/adoptium/temurin16-binaries/releases/download/jdk-16.0.2%2B7/OpenJDK16U-jdk_x64_windows_hotspot_16.0.2_7.zip',
        'url_linux':   'https://github.com/adoptium/temurin16-binaries/releases/download/jdk-16.0.2%2B7/OpenJDK16U-jdk_x64_linux_hotspot_16.0.2_7.tar.gz',
        'name': 'Temurin JDK 16'
    },
    {
        'mc_version': '0.0.0',
        'java_version': 8,
        'url_windows': 'https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u422-b05/OpenJDK8U-jdk_x64_windows_hotspot_8u422b05.zip',
        'url_linux':   'https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u422-b05/OpenJDK8U-jdk_x64_linux_hotspot_8u422b05.tar.gz',
        'name': 'Temurin JDK 8'
    },
]

def _build_mapping():
    """Construye JAVA_MAPPING con la URL correcta para la plataforma actual."""
    result = []
    is_windows = sys.platform == "win32"
    for entry in _JAVA_MAPPING_ALL:
        result.append({
            'mc_version':   entry['mc_version'],
            'java_version': entry['java_version'],
            'url':          entry['url_windows'] if is_windows else entry['url_linux'],
            'name':         entry['name'],
        })
    return result

JAVA_MAPPING = _build_mapping()