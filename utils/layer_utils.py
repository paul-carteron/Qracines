from qgis.core import *
from qgis.utils import *
from qgis.PyQt.QtCore import *
import json
import os

# Efface le projet en cours
def clear_qgis_project():
    project = QgsProject.instance()
    root = project.layerTreeRoot()

    # Supprime toutes les couches
    for layer in project.mapLayers().values():
        project.removeMapLayer(layer)

    # Supprime tous les groupes
    for group in root.children():
        if isinstance(group, QgsLayerTreeGroup):
            root.removeChildNode(group)
            
# Fonction pour charger des serveurs WMS configurés dans config.json
def import_wms_from_config(server_names, group_name=None):
    
    # Charge la configuration JSON
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Charge les serveurs WMS
    wms_servers = config.get("wms_servers", {})
    
    # Récupérer l'instance du projet QGIS et l'arbre des couches
    root = QgsProject.instance().layerTreeRoot()

    # Vérifier si un groupe doit être créé
    group = None
    if group_name:
        group = root.findGroup(group_name)
        if not group:
            group = root.addGroup(group_name)
    
    # Importe les serveurs
    for server_name in server_names:
        server_info = wms_servers.get(server_name)
        
        if server_info:
            display_name = server_info.get("display_name", server_name)
            url = server_info.get("url")
            wms_layer = QgsRasterLayer(url, display_name, "wms")
            if wms_layer.isValid():
                if group:
                    QgsProject.instance().addMapLayer(wms_layer,False)
                    group.addLayer(wms_layer)
                else:
                    QgsProject.instance().addMapLayer(wms_layer)

# Fonction pour importer des vecteurs configurés dans config.json
def import_vectors_from_config(styles_directory, forest_directory, directories_type, forest_prefix, vector_names, group_name=None):
    
    # Charge la configuration JSON
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Charge le répertoire configuré
    directories = config["directories"].get(directories_type)
    vectors_directory = directories["vectors"]
    
    # Récupérer l'instance du projet QGIS et l'arbre des couches
    root = QgsProject.instance().layerTreeRoot()

    # Vérifier si un groupe doit être créé
    group = None
    if group_name:
        group = root.findGroup(group_name)
        if not group:
            group = root.addGroup(group_name)

    # Importer chaque couche dans la liste de noms de couches
    for vector_name in vector_names:
        # Charge le vecteur
        vector_info  = config["vectors"].get(vector_name)
        if vector_info:
            file = vector_info["file"]
            call = vector_info["call"]
            style = vector_info["style"]
        
        # Construire le chemin vers le fichier de la couche
        vector_file = forest_prefix + "_" + file + ".shp"
        vector_path = os.path.join(forest_directory, vectors_directory, vector_file)

        # Importer la couche vecteur
        vector_layer = QgsVectorLayer(vector_path, call, "ogr")
        if vector_layer.isValid():
          if group:
              QgsProject.instance().addMapLayer(vector_layer,False)
              group.addLayer(vector_layer)
          else:
              QgsProject.instance().addMapLayer(vector_layer)

          # Appliquer le style depuis le répertoire des styles
          style_file = style + ".qml"
          style_path = os.path.join(styles_directory, style_file)
          vector_layer.loadNamedStyle(style_path)

# Fonction pour importer des couches d'un gpkg configurés dans config.json       
def import_layers_from_gpkg(styles_directory, forest_directory, directories_type, forest_prefix, gpkg_name, layers_names, group_name=None):
    # Charge la configuration JSON
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Charge le répertoire configuré
    directories = config["directories"].get(directories_type)
    gpkg_directory = directories["others"]

    # Récupérer l'instance du projet QGIS et l'arbre des couches
    root = QgsProject.instance().layerTreeRoot()

    # Vérifier si un groupe doit être créé
    group = None
    if group_name:
        group = root.findGroup(group_name)
        if not group:
            group = root.addGroup(group_name)

    # Chemin vers le GeoPackage
    gpkg_path = os.path.join(forest_directory, gpkg_directory, forest_prefix + "_" + gpkg_name + ".gpkg")

    # Créer un Uri de connexion pour le GeoPackage
    uri = QgsDataSourceUri()
    uri.setDatabase(gpkg_path)

    # Importer chaque couche dans la liste de noms de couches
    for layer_name in layers_names:
        # Vérifier si la couche existe dans le GeoPackage
        vector_layer = QgsVectorLayer(uri.uri() + "|layername=" + layer_name, layer_name, "ogr")
        
        if not vector_layer.isValid():
            print(f"Layer {layer_name} non valide ou non trouvée.")
            continue
        
        # Ajouter la couche au projet
        if group:
            QgsProject.instance().addMapLayer(vector_layer, False)
            group.addLayer(vector_layer)
        else:
            QgsProject.instance().addMapLayer(vector_layer)

        # Appliquer le style depuis le répertoire des styles
        style_info = config["others"].get(gpkg_name, {}).get(layer_name)
        if style_info:
            style = style_info.get("style")
            if style:
                style_file = style + ".qml"
                style_path = os.path.join(styles_directory, style_file)
                vector_layer.loadNamedStyle(style_path)

# Fonction pour récupérer le lien vers un vecteur configuré
def get_vector_from_config(forest_directory, directories_type, forest_prefix, vector_name):
    
    # Charge la configuration JSON
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Charge le répertoire configuré
    directories = config["directories"].get(directories_type)
    vectors_directory = directories["vectors"]
    vector_info  = config["vectors"].get(vector_name)
    if vector_info:
            file = vector_info["file"]
    vector_file = forest_prefix + "_" + file + ".shp"
    vector_path = os.path.join(forest_directory, vectors_directory, vector_file)
    
    return(vector_path)

# Fonction pour importer des rasters configurés dans config.json
def import_rasters_from_config(styles_directory, forest_directory, directories_type, forest_prefix, raster_names, group_name=None):
    
    # Charge la configuration JSON
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Charge le répertoire configuré
    directories = config["directories"].get(directories_type)
    rasters_directory = directories["rasters"]

    # Récupérer l'instance du projet QGIS et l'arbre des couches
    root = QgsProject.instance().layerTreeRoot()

    # Vérifier si un groupe doit être créé
    group = None
    if group_name:
        group = root.findGroup(group_name)
        if not group:
            group = root.addGroup(group_name)

    # Importer chaque raster dans la liste de noms de couches
    for raster_name in raster_names:
        # Charge les infos du raster depuis la config
        raster_info = config["rasters"].get(raster_name)
        if raster_info:
            file = raster_info["file"]
            style = raster_info["style"]

        # Construire le chemin vers le fichier raster
        raster_file = forest_prefix + "_" + file + ".tif"
        raster_path = os.path.join(forest_directory, rasters_directory, raster_file)

        # Importer la couche raster
        raster_layer = QgsRasterLayer(raster_path, raster_name)
        if raster_layer.isValid():
            if group:
                QgsProject.instance().addMapLayer(raster_layer, False)
                group.addLayer(raster_layer)
            else:
                QgsProject.instance().addMapLayer(raster_layer)

            # Appliquer le style depuis le répertoire des styles s'il est défini
            if style:
                style_file = style + ".qml"
                style_path = os.path.join(styles_directory, style_file)
                if os.path.exists(style_path):
                    raster_layer.loadNamedStyle(style_path)
                    raster_layer.triggerRepaint()
                    
# Fonction pour récupérer des listes configurées
def get_list_from_config(clef, data=None):
  
    # Charge la configuration JSON
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Récupère les données
    if data is None:
        return config.get(clef, {})
    else:
        return config.get(clef, {}).get(data, [])

# Fonction zoom sur emprise
def zoom_on_layer(layer_name):
    layer = QgsProject.instance().mapLayersByName(layer_name)[0]
    canvas = iface.mapCanvas()
    extent = layer.extent()
    canvas.setExtent(extent)
  
# Fonctions de visibilité des couches
def visibility_on_layer(layer_name, visibility):
    layer = QgsProject.instance().mapLayersByName(layer_name)
    if layer:
        layer = layer[0]
        layer_node = QgsProject.instance().layerTreeRoot().findLayer(layer.id())
        if layer_node:
            layer_node.setItemVisibilityChecked(visibility)

def visibility_on_layers(layers, visibility):
    for layer in layers:
        visibility_on_layer(layer, visibility)

# Fonction de création de thème
def create_map_theme(theme_name, visible_layers, invisible_layers):
    visibility_on_layers(visible_layers, True)
    visibility_on_layers(invisible_layers, False)
    map_theme = QgsMapThemeCollection.createThemeFromCurrentState(QgsProject.instance().layerTreeRoot(), iface.layerTreeView().layerTreeModel())
    QgsProject.instance().mapThemeCollection().insert(theme_name, map_theme)

# Fonction pour recharger les styles
def style_on_layers(layers, style_directory):
    project = QgsProject.instance()
    for layer_name in layers:
        matching_layers = project.mapLayersByName(layer_name)
        if matching_layers:
            layer = matching_layers[0]
            style_path = os.path.join(style_directory, layer_name + ".qml")
            if layer.loadNamedStyle(style_path):
                layer.triggerRepaint()
                
# Réduire les couches  
def replier():
    root = QgsProject.instance().layerTreeRoot()
    for node in root.children():
        node.setExpanded(False)  # Replie le groupe ou la couche
        if isinstance(node, QgsLayerTreeGroup):  # Si c'est un groupe, on repli ses enfants aussi
            for enfant in node.children():
                enfant.setExpanded(False)
                
# Opacité
def customize(layer_name):
    layer = QgsProject.instance().mapLayersByName(layer_name)[0]
    if layer.isValid():
        layer.setOpacity(0.5)
