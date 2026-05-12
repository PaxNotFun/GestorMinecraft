from .base_installer import BaseInstaller
from .vanilla_installer import VanillaInstaller
from .paper_installer import PaperInstaller
from .folia_installer import FoliaInstaller
from .forge_installer import ForgeInstaller
from .fabric_installer import FabricInstaller


def get_installer(sinfo, spath, app_instance, progress_callback, is_reinstall=False, reinstall_mode='partial', is_update=False):
    """Factory para obtener el instalador correcto según el tipo de servidor."""
    installers_map = {
        "Vanilla": VanillaInstaller,
        "PaperMC": PaperInstaller,
        "Folia": FoliaInstaller,
        "Forge": ForgeInstaller,
        "Fabric": FabricInstaller
    }

    installer_class = installers_map.get(sinfo['type'])
    if not installer_class:
        raise Exception(f"Tipo de servidor '{sinfo['type']}' no soportado.")

    return installer_class(sinfo, spath, app_instance, progress_callback, is_reinstall, reinstall_mode, is_update)