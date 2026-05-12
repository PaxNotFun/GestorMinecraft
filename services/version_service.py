import requests

from config.defaults import DEFAULT_TIMEOUT
from config.urls import PAPERMC_API_URL, FOLIA_API_URL, VANILLA_API_URL, FORGE_API_URL, FABRIC_META_URL

HEADERS = {'User-Agent': 'GetMineHub'}


def _check_vanilla(mc_version):
    try:
        response = requests.get(VANILLA_API_URL, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        return any(v['id'] == mc_version for v in response.json()['versions'])
    except (requests.exceptions.RequestException, KeyError):
        return False


def _check_papermc(mc_version):
    try:
        response = requests.get(
            f"{PAPERMC_API_URL}/versions/{mc_version}",
            headers=HEADERS,
            timeout=DEFAULT_TIMEOUT
        )
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def _check_folia(mc_version):
    try:
        response = requests.get(
            f"{FOLIA_API_URL}/versions/{mc_version}",
            headers=HEADERS,
            timeout=DEFAULT_TIMEOUT
        )
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def _check_forge(mc_version):
    try:
        response = requests.get(FORGE_API_URL, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        promos = response.json().get('promos', {})
        return f"{mc_version}-latest" in promos or f"{mc_version}-recommended" in promos
    except (requests.exceptions.RequestException, KeyError):
        return False


def _check_fabric(mc_version):
    try:
        response = requests.get(
            f"{FABRIC_META_URL}/versions/game",
            headers=HEADERS,
            timeout=DEFAULT_TIMEOUT
        )
        response.raise_for_status()
        return any(v['version'] == mc_version for v in response.json())
    except (requests.exceptions.RequestException, KeyError):
        return False


def is_version_valid(server_type, mc_version):
    """Verifica si una versión de servidor es válida para un tipo de servidor."""
    if not mc_version:
        return False

    checkers = {
        "Vanilla": _check_vanilla,
        "PaperMC": _check_papermc,
        "Folia": _check_folia,
        "Forge": _check_forge,
        "Fabric": _check_fabric
    }

    checker = checkers.get(server_type)
    return checker(mc_version) if checker else False