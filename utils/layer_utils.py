from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsMessageLog,
    Qgis,
    QgsLayerTreeGroup,
    QgsMapThemeCollection,
    QgsCoordinateReferenceSystem,
    QgsFields,
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

# endregion

def zoom_on_layer(key):
    layer = QgsProject.instance().mapLayersByName(get_display_name(key))[0]
    canvas = iface.mapCanvas()
    extent = layer.extent()
    canvas.setExtent(extent)

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
