from qgis.core import Qgis

def show_message(iface, level: str = "info", message: str, duration: int = 10) -> None:
    """
    Affiche un message dans la barre d'état de QGIS via iface.messageBar().
    
    :param iface: L'interface QGIS (habituellement passée depuis le plugin, ex. self.iface)
    :param message: Le texte à afficher
    :param level: Niveau de message ('info', 'success', 'warning', 'critical')
    :param duration: Durée d'affichage en secondes
    """
    levels = {
        "info": Qgis.Info,
        "success": Qgis.Success,
        "warning": Qgis.Warning,
        "critical": Qgis.Critical
    }
    
    qgis_level = levels.get(level.lower(), Qgis.Info)
    iface.messageBar().pushMessage("Qsequoia2", message, level=qgis_level, duration=duration)
