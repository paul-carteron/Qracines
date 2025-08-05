from qgis.core import Qgis

def show_message(iface, message: str, level: str = "info", duration: int = 10) -> None:
    """
    Affiche un message dans la barre d'état de QGIS via iface.messageBar().

    :param iface: Interface QGIS (ex. self.iface)
    :param message: Texte à afficher
    :param level: 'info', 'success', 'warning', 'critical'
    :param duration: Durée en secondes
    """
    levels = {
        "info": Qgis.Info,
        "success": Qgis.Success,
        "warning": Qgis.Warning,
        "critical": Qgis.Critical,
    }
    qgis_level = levels.get(level.lower(), Qgis.Info)
    try:
        iface.messageBar().pushMessage("Qsequoia2", message, level=qgis_level, duration=duration)
    except Exception:
        print(f"[{level.upper()}] {message}")
