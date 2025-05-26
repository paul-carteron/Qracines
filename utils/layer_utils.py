from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsMessageLog,
    Qgis,
    QgsLayerTreeGroup,
    QgsMapThemeCollection,
    QgsRelation
)
from qgis.utils import iface
from osgeo import ogr

from .path_manager import get_wms, get_style, get_path, get_display_name, get_wms

# region LOAD LAYERS

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
        if project.mapLayersByName(display_name):
            QgsMessageLog.logMessage(f"Layer '{display_name}' already loaded, skipping.", "Qsequoia2", Qgis.Info)
            continue

        layer = QgsRasterLayer(str(url), display_name, "wms")

        if not layer.isValid():
            QgsMessageLog.logMessage(f"Failed to load WMS '{key}' from {url}", "Qsequoia2", Qgis.Warning)
            continue

        # add to project, optionally hide it from the legend
        project.addMapLayer(layer, not bool(group))

        if group:
            group.addLayer(layer)

def load_vectors(*vector_keys, group_name=None):
    """
    Load vector layers by key into the project. Create group only if at least one is valid.
    Returns a list of successfully loaded keys.
    """
    project = QgsProject.instance()
    root = project.layerTreeRoot()
    group = None
    loaded_keys = []

    for key in vector_keys:
        display_name = get_display_name(key)

        # Skip if already loaded
        if project.mapLayersByName(display_name):
            QgsMessageLog.logMessage(f"Layer '{display_name}' already loaded, skipping.", "Qsequoia2", Qgis.Info)
            continue

        path = get_path(key)
        layer = QgsVectorLayer(str(path), display_name, "ogr")

        # Skip invalid layers
        if not layer.isValid():
            QgsMessageLog.logMessage(f"Failed to load vector '{key}' from {path}", "Qsequoia2", Qgis.Warning)
            continue

        # Create group only if a layer will be added
        if group_name and group is None:
            group = root.findGroup(group_name) or root.addGroup(group_name)

        project.addMapLayer(layer, not bool(group))
        if group:
            group.addLayer(layer)

        try:
            style_path = get_style(key)
            layer.loadNamedStyle(str(style_path))
        except Exception as e:
            QgsMessageLog.logMessage(f"Could not style '{key}': {e}", "Qsequoia2", Qgis.Warning)

        layer.triggerRepaint()
        loaded_keys.append(key)

    return loaded_keys

def load_rasters(*raster_keys, group_name=None):
    """
    Load raster layers by key into the project. Create group only if at least one is valid.
    """
    project = QgsProject.instance()
    root = project.layerTreeRoot()
    group = None
    loaded_keys = []

    for key in raster_keys:
        display_name = get_display_name(key)

        # Skip already loaded
        if project.mapLayersByName(display_name):
            QgsMessageLog.logMessage(f"Layer '{display_name}' already loaded, skipping.", "Qsequoia2", Qgis.Info)
            continue

        path = get_path(key)
        layer = QgsRasterLayer(str(path), display_name)

        # Skip invalid layers
        if not layer.isValid():
            QgsMessageLog.logMessage(f"Invalid raster '{key}' at {path}", "Qsequoia2", Qgis.Warning)
            continue
        
        loaded_keys.append(key)

        # Create group only when actually needed
        if group_name and group is None:
            group = root.findGroup(group_name) or root.addGroup(group_name)

        project.addMapLayer(layer, not bool(group))
        if group:
            group.addLayer(layer)

        # Try styling
        try:
            style_path = get_style(key)
            layer.loadNamedStyle(str(style_path))
        except Exception as e:
            QgsMessageLog.logMessage(f"Styling failed for '{key}': {e}", "Qsequoia2", Qgis.Warning)

        layer.triggerRepaint()

    return loaded_keys

# endregion

def zoom_on_layer(key):
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

def _set_layer_visibility(layer_name, visible):
    project = QgsProject.instance()
    layers = project.mapLayersByName(layer_name)
    if not layers:
        QgsMessageLog.logMessage(f"Layer '{layer_name}' not found for visibility toggle", "Qsequoia2", Qgis.Warning)
        return
    
    node = project.layerTreeRoot().findLayer(layers[0].id())
    if node:
        node.setItemVisibilityChecked(visible)

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
         
def replier():
    root = QgsProject.instance().layerTreeRoot()
    for node in root.children():
        node.setExpanded(False)  # Replie le groupe ou la couche
        if isinstance(node, QgsLayerTreeGroup):  # Si c'est un groupe, on repli ses enfants aussi
            for enfant in node.children():
                enfant.setExpanded(False)

def add_layers_from_gpkg(gpkg_path, *layer_names):
    datasource = ogr.Open(gpkg_path)
    if datasource is None:
        raise Exception("Failed to open GeoPackage.")

    available_layers = [layer.GetName() for layer in datasource]

    # If no layer names provided, load all
    layers_to_load = layer_names or available_layers

    for layer in reversed(available_layers):
        if layer not in layers_to_load:
            continue

        uri = f"{gpkg_path}|layername={layer}"
        vlayer = QgsVectorLayer(uri, layer, 'ogr')
        if vlayer.isValid():
            QgsProject.instance().addMapLayer(vlayer)
            print(f"✅ Layer '{layer}' added to project")
        else:
            print(f"❌ Layer '{layer}' is not valid and was skipped")

def create_relation(parent_name, child_name, parent_field, child_field, relation_id, relation_name):
    parent_layer = QgsProject.instance().mapLayersByName(parent_name)[0]
    child_layer = QgsProject.instance().mapLayersByName(child_name)[0]
    
    if parent_layer and child_layer:
       relation = QgsRelation()
       relation.setId(relation_id)
       relation.setName(relation_name)
       relation.setReferencedLayer(parent_layer.id())
       relation.setReferencingLayer(child_layer.id())
       relation.addFieldPair(child_field, parent_field)
       relation.setStrength(QgsRelation.Composition)
       
       if relation.isValid():
          QgsProject.instance().relationManager().addRelation(relation)

def set_layers_readonly(*keys):
    for key in keys:
        name = get_display_name(key)
        layer = QgsProject.instance().mapLayersByName(name)
        if layer:
            vector_layer = layer[0]
            if isinstance(vector_layer, QgsVectorLayer):
                vector_layer.setReadOnly(True)
