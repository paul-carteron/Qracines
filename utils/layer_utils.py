from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsMessageLog,
    Qgis,
    QgsLayerTreeGroup,
    QgsMapThemeCollection
)
from qgis.utils import iface

from .path_manager import get_wms, get_style, get_path, get_display_name, get_wms

def load_wms(*wms_keys, group_name = None):
    """
    Load WMS layers by key (from wms.yaml) into the project.
    If group_name is given, layers go into that group (hidden at root); 
    otherwise they appear at the root legend.
    """
    project = QgsProject.instance()
    root = project.layerTreeRoot()

    # find or create the target group
    group = None
    if group_name:
        group = root.findGroup(group_name) or root.addGroup(group_name)

    for key in wms_keys:
        display_name, url = get_wms(key)
        layer = QgsRasterLayer(str(url), display_name, "wms")

        if not layer.isValid():
            QgsMessageLog.logMessage(f"Failed to load WMS '{key}' from {url}", "Qsequoia2", Qgis.Warning)
            continue

        # add to project, optionally hide it from the legend
        project.addMapLayer(layer, not bool(group))

        if group:
            group.addLayer(layer)

def load_vectors(*vector_keys, group_name = None):
    """
    Load vector layers by key (from sig_structure.yaml) into the project.
    If group_name is given, layers go into that group (hidden at root);
    otherwise they appear at the root legend. Styles (if defined) are applied.
    """
    project = QgsProject.instance()
    root = project.layerTreeRoot()

    group = None
    if group_name:
        group = root.findGroup(group_name) or root.addGroup(group_name)
    
    for key in vector_keys:
        path = get_path(key)
        display_name = get_display_name(key)
        layer = QgsVectorLayer(str(path), display_name, "ogr")

        if not layer.isValid():
            QgsMessageLog.logMessage(f"Failed to load vector '{key}' from {path}", "Qsequoia2", Qgis.Warning)
            continue

        project.addMapLayer(layer, not bool(group))
        if group:
            group.addLayer(layer)

        try:
            style_path = get_style(key)
            layer.loadNamedStyle(str(style_path))
            layer.triggerRepaint()
        except Exception as e:
            QgsMessageLog.logMessage(f"Could not style '{key}': {e}", "Qsequoia2", Qgis.Warning)

def load_rasters(*raster_keys, group_name = None):
    """
    Load raster layers by key (from sig_structure.yaml) into the project.
    If group_name is given, layers go into that group (hidden at root);
    otherwise they appear at the root legend. Styles (if defined) are applied.
    """
    project = QgsProject.instance()
    root = project.layerTreeRoot()

    group = None
    if group_name:
        group = root.findGroup(group_name) or root.addGroup(group_name)
    
    for key in raster_keys:
        path = get_path(key)
        display_name = get_display_name(key)
        layer = QgsRasterLayer(str(path), display_name)

        if not layer.isValid():
            QgsMessageLog.logMessage(f"Failed to load vector '{key}' from {path}", "Qsequoia2", Qgis.Warning)
            continue

        project.addMapLayer(layer, not bool(group))
        if group:
            group.addLayer(layer)

        try:
            style_path = get_style(key)
            layer.loadNamedStyle(str(style_path))
            layer.triggerRepaint()
        except Exception as e:
            QgsMessageLog.logMessage(f"Could not style '{key}': {e}", "Qsequoia2", Qgis.Warning)



# Fonction zoom sur emprise
def zoom_on_layer(key):
    layer = QgsProject.instance().mapLayersByName(get_display_name(key))[0]
    canvas = iface.mapCanvas()
    extent = layer.extent()
    canvas.setExtent(extent)
  
# Fonctions de visibilité des couches
def _set_layer_visibility(layer_name, visible):
    project = QgsProject.instance()
    layers = project.mapLayersByName(layer_name)
    if not layers:
        QgsMessageLog.logMessage(f"Layer '{layer_name}' not found for visibility toggle", "Qsequoia2", Qgis.Warning)
        return
    
    node = project.layerTreeRoot().findLayer(layers[0].id())
    if node:
        node.setItemVisibilityChecked(visible)

# Fonction de création de thème
def create_map_theme(theme_name, visible_keys, invisible_keys):
    def _resolve_name(key):
        try:
            return get_display_name(key)
        except KeyError:
            # fallback to WMS
            name, _url = get_wms(key)
            return name


    for key in visible_keys:
        layer_name = _resolve_name(key)
        _set_layer_visibility(layer_name, True)

    for key in invisible_keys:
        layer_name = _resolve_name(key)
        _set_layer_visibility(layer_name, False)

    project = QgsProject.instance()
    root = project.layerTreeRoot()
    map_theme = QgsMapThemeCollection.createThemeFromCurrentState(root, iface.layerTreeView().layerTreeModel())
    project.mapThemeCollection().insert(theme_name, map_theme)
         
# Réduire les couches  
def replier():
    root = QgsProject.instance().layerTreeRoot()
    for node in root.children():
        node.setExpanded(False)  # Replie le groupe ou la couche
        if isinstance(node, QgsLayerTreeGroup):  # Si c'est un groupe, on repli ses enfants aussi
            for enfant in node.children():
                enfant.setExpanded(False)

