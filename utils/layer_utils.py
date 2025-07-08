import yaml
from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsMessageLog,
    Qgis,
    QgsLayerTreeGroup,
    QgsMapThemeCollection,
    QgsRelation,
    QgsEditorWidgetSetup,
    QgsSnappingConfig,
    QgsTolerance
)
from qgis.utils import iface
from osgeo import ogr

from .path_manager import get_wms, get_style, get_path, get_display_name, get_wms, get_config_path

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
        
        print(f"load_raster - key: {key}")
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

def load_gpkg(gpkg_path, *layers, group_name=None):
    datasource = ogr.Open(gpkg_path)
    if datasource is None:
        raise Exception("Failed to open GeoPackage.")

    project = QgsProject.instance()
    root = project.layerTreeRoot()
    group = None
    if group_name:
        group = root.findGroup(group_name) or root.addGroup(group_name)

    available_layers = [layer.GetName() for layer in datasource]

    # If no layer names provided, load all
    layers_to_load = layers or available_layers

    for layer in layers_to_load:
        if layer not in available_layers:
            continue

        uri = f"{gpkg_path}|layername={layer}"
        imported_layer = QgsVectorLayer(uri, layer, 'ogr')
        # Skip invalid layers
        if not imported_layer.isValid():
            QgsMessageLog.logMessage(f"Failed to load gpkg from {gpkg_path}", "Qsequoia2", Qgis.Warning)
            continue

        # Create group only if a layer will be added
        if group_name and group is None:
            group = root.findGroup(group_name) or root.addGroup(group_name)

        project.addMapLayer(imported_layer, not bool(group))
        if group:
            group.addLayer(imported_layer)

    return None
    
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

def deplier(group_name):
    root = QgsProject.instance().layerTreeRoot()
    group = root.findGroup(group_name)
  
    if group:
        group.setExpanded(True)

def create_relation(parent_name, child_name, parent_field, child_field, relation_id, relation_name):
    """
    Crée une relation de composition et configure le champ child_field pour RelationReference.
    Version simple sans gestion d'exception.
    """
    proj = QgsProject.instance()
    parent_layers = proj.mapLayersByName(parent_name)
    child_layers = proj.mapLayersByName(child_name)
    if not parent_layers or not child_layers:
        print(f"Couche parent '{parent_name}' ou enfant '{child_name}' introuvable")
        return False
    parent_layer = parent_layers[0]
    child_layer = child_layers[0]

    # Création de la relation
    relation = QgsRelation()
    relation.setId(relation_id)
    relation.setName(relation_name)
    relation.setReferencedLayer(parent_layer.id())
    relation.setReferencingLayer(child_layer.id())
    relation.addFieldPair(child_field, parent_field)
    relation.setStrength(QgsRelation.Composition)

    if not relation.isValid():
        print(f"Relation invalide pour ID '{relation_id}'")
        return False

    proj.relationManager().addRelation(relation)

    # Configuration du widget RelationReference
    child_layer.updateFields()
    idx = child_layer.fields().indexOf(child_field)
    if idx == -1:
        print(f"Champ '{child_field}' introuvable dans la couche '{child_name}'")
        return True  # relation créée, mais widget non configuré

    config = {
        'Relation': relation_id,
        'AllowAddFeatures': False,
        'AllowNULL': False,
        'FetchLimitActive': True,
        'FetchLimitNumber': 100,
        'MapIdentification': False,
        'ReadOnly': False,
        'ReferencedLayerDataSource': parent_layer.source(),
        'ReferencedLayerId': parent_layer.id(),
        'ReferencedLayerName': parent_layer.name(),
        'ReferencedLayerProviderKey': parent_layer.providerType(),
        'ShowForm': False,
        'ShowOpenFormButton': True
    }
    setup = QgsEditorWidgetSetup('RelationReference', config)
    child_layer.setEditorWidgetSetup(idx, setup)

    print(f"Relation '{relation_id}' créée et widget configuré sur '{child_name}.{child_field}'")
    return True

def set_layers_readonly(*keys):
    for key in keys:
        name = get_display_name(key)
        layer = QgsProject.instance().mapLayersByName(name)
        if layer:
            vector_layer = layer[0]
            if isinstance(vector_layer, QgsVectorLayer):
                vector_layer.setReadOnly(True)

def create_map_project(map_project, type_project, layer_registry=None):
    
    # Lecture du YAML
    cfg_path = get_config_path("map_project.yaml")
    with open(cfg_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Construction du nom de projet
    project_key = map_project.lower() + "_" + type_project
    print(f"project_key projet : {project_key}")

    # Test d'existence dans le YAML au bon niveau
    map_projects = config.get('map_project', {})
    if project_key not in map_projects:
        type_project = "wooded"
        project_key = map_project.lower() + "_" + type_project
        print(f"project_key retenue : {project_key}")
    
    # Lecture du projet
    map_data = map_projects.get(project_key)
    if not map_data:
        raise ValueError(f"Le projet '{project_key}' n'existe pas dans le fichier YAML.")

    # Ajoute groupes vector, sequoia, wms
    for group_type in ['vector', 'sequoia', 'wms']:
        group_info = map_data.get(group_type)
        if not group_info:
            continue

        group_name = group_info.get('group_name')
        group_zoom = group_info.get('zoom')
        group_layers = group_info.get('layers', [])

        if group_layers:
            if group_type in ['vector', 'sequoia']:
                load_vectors(*group_layers, group_name=group_name)
            else:
                load_wms(*group_layers, group_name=group_name)

        if group_zoom:
            zoom_on_layer(group_zoom)
    
    # Gestion des groupes
    replier()
    deplier("sequoia")
    
    # Gestion des thèmes
    themes = map_data.get('themes', [])
    for theme in themes:
        theme_name = f"{theme['name']}"
        visible_keys = theme.get('visible', [])
        invisible_keys = theme.get('hidden', [])
        create_map_theme(theme_name, visible_keys, invisible_keys)

    # scan25grey
    layer = QgsProject.instance().mapLayersByName("IGN SCAN 25 TOPO (Metropole) gray")
    if layer:
        layer[0].setOpacity(0.5)

def configure_snapping(layer_names=None):
    project = QgsProject.instance()
    config = project.snappingConfig()

    # 1. Activer l'accrochage global
    config.setEnabled(True)
    # config.setMode(Qgis.SnappingMode.AllLayers)
    # config.setMode(Qgis.SnappingMode.AdvancedConfiguration)

    # 2. Réglages globaux (pour tolérance, types…)
    snapping_types = Qgis.SnappingTypes(
        Qgis.SnappingType.Vertex |
        Qgis.SnappingType.Segment |
        Qgis.SnappingType.MiddleOfSegment |
        Qgis.SnappingType.LineEndpoint
    )
    config.setTypeFlag(snapping_types)
    config.setTolerance(15)
    config.setUnits(QgsTolerance.Pixels)
    project.setTopologicalEditing(True)
    config.setIntersectionSnapping(True)
    config.setSelfSnapping(False)
    
    # 3. Définir la liste des couches ciblées
    if not layer_names:
        layers = [
            layer for layer in project.mapLayers().values()
            if isinstance(layer, QgsVectorLayer)
        ]
    else:
        layers = []
        for name in layer_names:
            display_name = get_display_name(name)
            matched = project.mapLayersByName(display_name)
            if not matched:
                print(f"⚠️ Couche non trouvée : {name}")
            else:
                layers.append(matched[0])
                
                
    # 4. Appliquer les réglages individuels
    config.clearIndividualLayerSettings()
    for layer in layers:
        settings = QgsSnappingConfig.IndividualLayerSettings(
            True,
            snapping_types,
            15.0,
            Qgis.MapToolUnit.Pixels
        )
        config.setIndividualLayerSettings(layer, settings)

    # 5. Appliquer la configuration globale
    project.setSnappingConfig(config)
