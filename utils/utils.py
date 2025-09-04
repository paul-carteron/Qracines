from qgis.core import Qgis, QgsProject, QgsMessageLog, QgsLayerTreeGroup, QgsCoordinateReferenceSystem, QgsMapThemeCollection
from qgis.utils import iface

from .layers import load_vectors, load_wms, set_layers_readonly
from .config import get_wms, get_display_name, get_wms, get_project_canvas

def create_theme(name: str, visible_keys: list[str]) -> None:

    # 1. Resolve display names once
    def _resolve_layer_name(key: str) -> str:
        # try alias lookup
        try:
            return get_display_name(key)   # vector/alias
        except KeyError:
            pass

        # try WMS lookup
        try:
            layer_name, _ = get_wms(key)   # WMS fallback
            return layer_name
        except KeyError:
            pass

        # final fallback: assume it's already a layer name
        return key
        
    resolved_names = {_resolve_layer_name(key) for key in visible_keys}

    # 2. Prepare project and theme objects
    proj = QgsProject.instance()
    mtc = proj.mapThemeCollection()
    theme_state = QgsMapThemeCollection.MapThemeRecord()

    # 3. Build a name→layer map in one pass
    layers = proj.mapLayers()
    name_to_layer = {ly.name(): ly for ly in layers.values()}

    # 4. Add only the matching layers
    for layer_name in resolved_names:
        layer = name_to_layer.get(layer_name)
        if layer:
            rec = QgsMapThemeCollection.MapThemeLayerRecord(layer)
            theme_state.addLayerRecord(rec)

    # 5. Insert the completed theme
    mtc.insert(name, theme_state)
    
    root  = proj.layerTreeRoot()
    model = iface.layerTreeView().layerTreeModel()
    mtc.applyTheme(name, root, model)

def create_project(project_key):
    loading_function = {
        "vector" : load_vectors,
        "wms" : load_wms
    }
    
    canvas_cfg = get_project_canvas(project_key)
    for g in canvas_cfg.groups:
        loader = loading_function.get(g.get("type"))
        layers = g.get("layers") or []
        loader(*layers, group_name=g.get("name"))
    
    set_layers_readonly(*canvas_cfg.readonly)

    for t in reversed(canvas_cfg.themes):
        create_theme(t.get("name"), t.get("show"))

    # Gestion des groupes
    replier()
    deplier("SEQUOIA")
    print("start zoom on")
    zoom_on(canvas_cfg.zoom_on)
    print("end zoom on")

    # Appliquer transparence sur la couche scan25grey si elle existe
    layer = QgsProject.instance().mapLayersByName(get_wms("wms_scan25_grey")[0])
    if layer:
        layer[0].setOpacity(0.5)

def clear_project(default_crs = 2154):
    proj = QgsProject.instance()

    proj.mapThemeCollection().clear()
    proj.layoutManager().clear()
    proj.layerTreeRoot().clear()
    proj.removeAllMapLayers()

    proj.setCrs(QgsCoordinateReferenceSystem.fromEpsgId(default_crs))

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

def zoom_on(key):
    layers = QgsProject.instance().mapLayersByName(get_display_name(key))
    if not layers:
        QgsMessageLog.logMessage(f"Layer '{key}' not found. Zoom skipped.", "Qsequoia2", Qgis.Warning)
        return

    layer = layers[0]
    if not layer.isValid():
        QgsMessageLog.logMessage(f"Layer '{key}' is not valid. Zoom skipped.", "Qsequoia2", Qgis.Warning)
        return

    canvas = iface.mapCanvas()
    canvas.setExtent(layer.extent())
    canvas.refresh()
      
def replier():
    root = QgsProject.instance().layerTreeRoot()
    for node in root.children():
        node.setExpanded(False)  # Replie le groupe ou la couche
        if isinstance(node, QgsLayerTreeGroup):  # Si c'est un groupe, on repli ses enfants aussi
            for enfant in node.children():
                enfant.setExpanded(False)

def deplier(group_name):
    root = QgsProject.instance().layerTreeRoot()
    group = root.findGroup(group_name)
  
    if group:
        group.setExpanded(True)
