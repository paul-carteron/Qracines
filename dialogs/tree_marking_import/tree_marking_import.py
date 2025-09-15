from PyQt5.QtWidgets import QMessageBox, QDialog
from .tree_marking_import_dialog import Ui_TreeMarkingImportDialog
from qgis.utils import iface
from qgis.core import QgsVectorLayer, QgsProcessing, QgsProject

# Import from utils folder
from ...utils.layers import get_path, load_gpkg
from ...utils.processing import calculate_essence_id, merge_with_ess, save_as_xlsx
from ...utils.ui import GpkgLoader
from ...core.layer_factory import LayerFactory

import processing

class TreeMarkingImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = QgsProject.instance()
        self.iface = iface
        self.ui = Ui_TreeMarkingImportDialog()  
        self.ui.setupUi(self)
        
        self.loader = GpkgLoader(ui = self.ui, add = 'pb_import_files', selected = 'lw_selected_files')

    def merge_files(self):
        if self.loader.is_valid():
            gpkgs = self.loader.selected_files

        out_path = get_path("inventaire")
        layers = LayerFactory.get_layer_names("INVENTAIRE")

        ess_layer_name = "essences"
        ess_layer = QgsVectorLayer(f"{gpkgs[0]}|layername={ess_layer_name}", ess_layer_name, "ogr")

        merged_layers = []
        for layer in layers:
            all_layer = []
            for gpkg in gpkgs:
                vl = QgsVectorLayer(f"{gpkg}|layername={layer}", layer, "ogr")
                if vl.isValid():
                    all_layer.append(vl)
            
            if not all_layer:
                print(f"Skipping '{layer}': no valid sources")
                continue
            
            merge_layer = processing.run("native:mergevectorlayers", {
                'LAYERS': all_layer,   # ← just reuse the list
                'CRS':    'PROJECT',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            })['OUTPUT']
 
            # When merging, fid is reinitialized which mean duplicated fid that will cause geopackage creation to fail (processing.run("native:package"))
            merge_layer = processing.run("qgis:deletecolumn", {
                'INPUT':  merge_layer,
                'COLUMN': ['fid'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            })['OUTPUT']

            merge_layer.setName(layer)
            merged_layers.append(merge_layer)

        
        merged_layers.append(ess_layer)
        merged_result = processing.run("native:package", {
            'LAYERS':      merged_layers,
            'OUTPUT':      str(out_path),
            'OVERWRITE':   True,
            'SAVE_STYLES': False
        })

        load_gpkg(merged_result['OUTPUT'], group_name="INVENTAIRE")

    def format_arbres(self):

        arbres_with_ess_id = calculate_essence_id(self.arbres, "ESSENCE_ID", "ESSENCE_SECONDAIRE_ID")
        arbres_with_ess = merge_with_ess(arbres_with_ess_id, self.ess)

        formated_tra = processing.run("qgis:refactorfields", {
            'INPUT': arbres_with_ess,
            'FIELDS_MAPPING': [
                {'expression': '"LOT"',         'name': 'LOT',         'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"PARCELLE"',    'name': 'PARCELLE',    'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"code"',        'name': 'CODE',        'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"essence"',     'name': 'ESSENCE',     'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"variation"',   'name': 'VARIATION',   'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"type"',        'name': 'TYPE',        'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"DIAMETRE"',    'name': 'DIAMETRE',    'type': 2,  'length': 10, 'precision': 3},
                {'expression': '"EFFECTIF"',    'name': 'EFFECTIF',    'type': 2,  'length': 10, 'precision': 0},
                {'expression': '"HAUTEUR"',     'name': 'HAUTEUR',     'type': 2,  'length': 10, 'precision': 3},
                {'expression': '"FAVORI"',      'name': 'FAVORI',      'type': 10, 'length': 10, 'precision': 3},
                {'expression': '"OBSERVATION"', 'name': 'OBSERVATION', 'type': 10, 'length': 10, 'precision': 3},
            ],
            'OUTPUT': 'memory:'
        })['OUTPUT']

        formated_tra.setName("transect")

        return formated_tra

    def accept(self):
        try:
            self.merge_files()

            self.arbres = self.project.mapLayersByName('arbres')[0]
            self.ess = self.project.mapLayersByName('essences')[0]

            formated_tra = self.format_arbres()

            out_path = get_path("inventaire_synthese")
            save_as_xlsx(formated_tra, path = out_path)
            
            QMessageBox.information(self, "Succès",  f"Géopackage(s) compilé(s) et extrait(s) dans :\n{out_path}")
            
            super().accept()

            return
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")