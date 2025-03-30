from PyQt5.QtWidgets import *
from .pedology_dialog import Ui_PedologyDialog
from qgis.core import *

# Import from utils folder
from ..utils.variable_utils import *
from ..utils.layer_utils import *
from ..utils.qfield_utils import *

def check_variables():
    styles_directory = get_global_variable("styles_directory")
    forest_directory = get_project_variable("forest_directory")
    forest_prefix = get_project_variable("forest_prefix")
    
    if not styles_directory or not forest_directory or not forest_prefix:
        iface.messageBar().pushMessage("QSequoia2", "Dossier Sequoia non paramêtrée", level=Qgis.Critical, duration=10)
        return False
    return True
    
def create_pedology():
    if not check_variables():
        return
    
    # Initialisation
    create_new_projet_with_variables()
    
    styles_directory = get_global_variable("styles_directory")
    forest_directory = get_project_variable("forest_directory")
    forest_prefix = get_project_variable("forest_prefix")
    
    # Vector import
    vector_layers = ['PROP_line', 'PROP-Diag_line', 'PF_line', 'PF-Diag_line', 'PF_polygon', 'SSPF_polygon', 'SSPF-Diag_polygon', 'UA_polygon']
    import_vectors_from_config(styles_directory, forest_directory, "new_directories", forest_prefix, vector_layers, group_name="VECTOR")
    
    # Raster import
    raster_layers = ['PLT','PLT-ANC','IRC','RGB','MNH','SCAN25']
    import_rasters_from_config(styles_directory, forest_directory, "new_directories", forest_prefix, raster_layers, "RASTER")
    replier()
    
    # Creation de la couche sondage
    sondage_fields = [("fid", QVariant.Int), 
          ("uuid", QVariant.String), 
          ("humus", QVariant.String), 
          ("topographie", QVariant.String),
          ("exposition", QVariant.String), 
          ("station", QVariant.String), 
          ("arret", QVariant.String), 
          ("photo", QVariant.String)]
    sondage_layer = create_memory_layer('sondage', sondage_fields, 'Point')
    
    # Creation de la couche horizons
    horizons_fields = [("fid", QVariant.Int), 
          ("sondage", QVariant.String), 
          ("type", QVariant.String), 
          ("epaisseur", QVariant.String),
          ("humidite", QVariant.String), 
          ("texture", QVariant.String), 
          ("couleur", QVariant.String), 
          ("structure", QVariant.String),
          ("compacite", QVariant.String),
          ("eg", QVariant.Bool),
          ("eg_taille", QVariant.String),
          ("eg_proportion", QVariant.Double),
          ("hm", QVariant.Bool),
          ("hm_tache", QVariant.String),
          ("hm_proportion", QVariant.Double),
          ("car", QVariant.Bool),
          ("car_localisation", QVariant.String),
          ("car_puissance", QVariant.String),
          ("profondeur", QVariant.String)]
    horizons_layer = create_memory_layer('horizons', horizons_fields)
    
    # Creation du gpkg
    gpkg_path = get_gpkg_path(styles_directory, forest_directory, "new_directories", forest_prefix, "pedology")

    if not os.path.exists(gpkg_path):
        layers = [sondage_layer, horizons_layer]
        for layer in layers:
            write_layer_to_gpkg(layer, gpkg_path)
    
    # Import du gpkg
    add_all_layers_from_gpkg(gpkg_path, styles_directory)
    move_layer_to_top('sondage')

    # Création de la relation
    create_relation('sondage', 'horizons', 'uuid', 'sondage', 'sondage_horizons','sondage')
    
    # Création des thêmes
    map_themes = [
            ("1_PLT",
             ['PLT', 'Limite de propriété b', 'Limite de parcelle b', 'Parcelle forestière', 'Sous-parcelle forestière b', 'Unité d analyse'],
             ['PLT-ANC', 'IRC', 'RGB', 'MNH', 'SCAN25', 'Limite de propriété w', 'Limite de parcelle w', 'Sous-parcelle forestière w']),
            ("2_PLT-ANC",
             ['PLT-ANC', 'Limite de propriété b', 'Limite de parcelle b', 'Parcelle forestière'], 
             ['PLT', 'IRC', 'RGB', 'MNH', 'SCAN25', 'Limite de propriété w', 'Limite de parcelle w', 'Sous-parcelle forestière b', 'Sous-parcelle forestière w', 'Unité d analyse']),
            ("3_IRC",
             ['IRC', 'Limite de propriété w', 'Limite de parcelle w', 'Parcelle forestière', 'Sous-parcelle forestière w', 'Unité d analyse'],
             ['PLT', 'PLT-ANC', 'RGB', 'MNH', 'SCAN25', 'Limite de propriété b', 'Limite de parcelle b', 'Sous-parcelle forestière b']),
            ("4_RGB",
             ['RGB', 'Limite de propriété w', 'Limite de parcelle w', 'Parcelle forestière', 'Sous-parcelle forestière w', 'Unité d analyse'],
             ['PLT', 'PLT-ANC', 'IRC', 'MNH', 'SCAN25', 'Limite de propriété b', 'Limite de parcelle b', 'Sous-parcelle forestière b']),
            ("5_MNH",
             ['MNH', 'Limite de propriété b', 'Limite de parcelle b', 'Parcelle forestière', 'Sous-parcelle forestière b', 'Unité d analyse'],
             ['PLT', 'PLT-ANC', 'IRC', 'RGB', 'SCAN25', 'Limite de propriété w', 'Limite de parcelle w', 'Sous-parcelle forestière w']),
            ("6_SCAN25",
             ['SCAN25', 'Limite de propriété b', 'Limite de parcelle b', 'Parcelle forestière', 'Sous-parcelle forestière b', 'Unité d analyse'],
             ['PLT', 'PLT-ANC', 'IRC', 'RGB', 'MNH', 'Limite de propriété w', 'Limite de parcelle w', 'Sous-parcelle forestière w'])
            ]
    for theme in map_themes:
        create_map_theme(*theme)
        
    # Verrouillage des couches
    layer_names = ['Limite de propriété b', 'Limite de propriété w', 'Limite de parcelle b', 'Limite de parcelle w',
                   'Parcelle forestière', 'Sous-parcelle forestière b', 'Sous-parcelle forestière w', 'Unité d analyse']
    set_layers_readonly(layer_names)
    
    # Enregistrement du projet
    project = QgsProject.instance()
    save_path = os.path.join(forest_directory, "SIG", "0_OUTPUT", "PEDOLOGY.qgz")
    project.write(save_path)
    project.write()
    iface.messageBar().pushMessage("QSequoia2", "PEDOLOGY généré avec succès", level=Qgis.Success, duration=10)
    
    # Création du paquet
    create_qfield_package(forest_directory, save_path)
