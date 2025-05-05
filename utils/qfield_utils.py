from qgis.core import *
from osgeo import *
from qgis.utils import *
import zipfile
import json
import os

def create_memory_layer(layer_name, fields_list, geometry = None, crs = "EPSG:2154"):

    if geometry:
        crs_obj = QgsCoordinateReferenceSystem(crs)
        geometry_str = f"{geometry}?crs={crs_obj.authid()}"
    else:
        geometry_str = "None"

    # Create the layer
    layer = QgsVectorLayer(geometry_str, layer_name, "memory")
    if not layer.isValid():
        print("Failed to create the layer!")
        return False

    # Add fields to the layer
    fields = QgsFields()
    for field_name, field_type in fields_list:
        fields.append(QgsField(field_name, field_type))
    layer.dataProvider().addAttributes(fields)
    layer.updateFields()

    return layer

# Fonction pour récupérer le gpkg configuré
def get_gpkg_path(styles_directory, forest_directory, directories_type, forest_prefix, gpkg_name):
    
    # Charge la configuration JSON
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
       config = json.load(f)

    # Charge le répertoire configuré
    directories = config["directories"].get(directories_type)
    others_directory = directories["others"]
    
    # Création du gpkg
    gpkg_file = forest_prefix + "_" + gpkg_name + ".gpkg"
    gpkg_path = os.path.join(forest_directory, others_directory, gpkg_file)
    
    return gpkg_path
  
# Fonction d'ajout de layer à un gpkg
def write_layer_to_gpkg(layer, gpkg_path):
    if layer is None:
        return
    
    # Set up writing options
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    options.fileEncoding = "UTF-8"
    options.layerName = layer.name()

    # Determine the action based on whether the GeoPackage exists
    if not os.path.exists(gpkg_path):
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
    else:
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
        
    # Write the layer to the GeoPackage
    transform_context = QgsProject.instance().transformContext()
    error = QgsVectorFileWriter.writeAsVectorFormatV3(
        layer,
        gpkg_path,
        transform_context,
        options
    )

    if error[0] != QgsVectorFileWriter.NoError:
           raise Exception(f"Error writing layer '{layer.name()}' to GeoPackage: {error[1]}")


# Fonction d'ajout de layer à un gpkg
def add_all_layers_from_gpkg(gpkg_path, styles_directory=None):
    gpkg_data = ogr.Open(gpkg_path)
    
    if not gpkg_data:
        return

    layers = [gpkg_data.GetLayer(i).GetName() for i in range(gpkg_data.GetLayerCount())]
    for layer in layers:
        vlayer = iface.addVectorLayer(f"{gpkg_path}|layername={layer}", layer, "ogr")
        if vlayer and styles_directory:
            style_path = os.path.join(styles_directory, f"{layer}.qml")
            if os.path.exists(style_path):
                vlayer.loadNamedStyle(style_path)
                vlayer.triggerRepaint()

# PAUL ------------------

# Fonction comme ci-dessus mais normalement plsu robuste car on évite d'utiliser iface
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

# Fonction déplaçant une couche tout en haut
def move_layer_to_top(layer_name):
    project = QgsProject.instance()
    root = project.layerTreeRoot()

    # Trouver la couche par son nom
    layer = None
    for lyr in project.mapLayers().values():
        if lyr.name() == layer_name:
            layer = lyr
            break

    if not layer:
        return

    # Trouver le noeud de la couche dans l'arbre
    layer_node = root.findLayer(layer.id())
    if not layer_node:
        return

    # Déplacer la couche en première position
    root.insertChildNode(0, layer_node.clone())
    root.removeChildNode(layer_node)

# Fonctiond de creation de relations
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
          
# Fonction verouillant les modifications des couches Vecteurs
def set_layers_readonly(layer_names):
    for name in layer_names:
        layer = QgsProject.instance().mapLayersByName(name)
        if layer:
            vector_layer = layer[0]
            if isinstance(vector_layer, QgsVectorLayer):
                vector_layer.setReadOnly(True)
                                    
# Fonction de création d'un paquet Qfield        
def create_qfield_package(forest_directory, project_path):

    # Charger la configuration JSON
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Charger le répertoire configuré depuis le fichier JSON
    directories = config["directories"].get("new_directories", {})

    # Définir le chemin du fichier ZIP de sortie
    output_zip_path = os.path.join(forest_directory, "pedology_qfield.zip")

    # Créer le fichier ZIP
    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Ajouter le projet QGIS
        zipf.write(project_path, os.path.basename(project_path))

        # Ajouter les fichiers des répertoires configurés
        for key, subdir in directories.items():
            dir_path = os.path.join(forest_directory, subdir)

            if os.path.exists(dir_path):
                for root, _, files in os.walk(dir_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, os.path.relpath(file_path, forest_directory))
    return output_zip_path

# Fonction affectant une liste au formulaire d'un champ d'une couche
def apply_value_list_to_field(layer_name, field_name, values_list):
    layer = QgsProject.instance().mapLayersByName(layer_name)[0]

    # Nettoyage des doublons tout en conservant l'ordre
    seen = set()
    unique_values = [v for v in values_list if not (v in seen or seen.add(v))]

    # Création du dictionnaire pour le ValueMap
    value_map = {v: v for v in unique_values}

    # Création du setup du widget ValueMap
    config = {'map': value_map}
    setup = QgsEditorWidgetSetup("ValueMap", config)

    # Récupère l'index du champ
    field_index = layer.fields().indexOf(field_name)

    if field_index == -1:
        raise ValueError(f"Champ '{field_name}' introuvable dans la couche '{layer_name}'.")

    # Application du widget au champ
    layer.setEditorWidgetSetup(field_index, setup)

    # Mise à jour de la couche (optionnel)
    layer.triggerRepaint()

def zip_folder_contents(folder_path, output_zip_path):
    """
    Zips all contents (files and subfolders) of folder_path
    into a zip archive at output_zip_path.
    
    The contents will be stored in the zip archive without the top-level folder.
    """
    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Walk the folder tree
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                # Get the relative path to avoid including the top-level folder
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)
    print(f"Created zip archive at {output_zip_path}")