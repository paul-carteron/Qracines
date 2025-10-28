from PyQt5.QtWidgets import QMessageBox, QDialog, QFileDialog
from .diagnostic_import_dialog import Ui_DiagnosticImportDialog
from qgis.utils import iface
from qgis.core import QgsVectorLayer, QgsProcessing, QgsProject

# Import from utils folder
from ...utils.layers import get_path, load_gpkg
from ...utils.processing import calculate_essence_id, merge_with_ess, save_as_xlsx
from ...utils.ui import GpkgLoader

from ...core.layer_factory import LayerFactory

from ..diagnostic_create.diagnostic_create_service import DiagnosticService

import processing

class DiagnosticImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = QgsProject.instance()
        self.iface = iface
        self.ui = Ui_DiagnosticImportDialog()  
        self.ui.setupUi(self)
        
        self.loader = GpkgLoader(ui = self.ui, add = 'pb_import_files', selected = 'lw_selected_files')

    def merge_files(self):
        if self.loader.is_valid():
            gpkgs = self.loader.selected_files

        out_path = get_path("diag")
        layers = LayerFactory.get_layer_names("DIAGNOSTIC")

        ess_layer_name = "Essences"
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

        self.outpath = merged_result['OUTPUT']
        
        return None
    
    def load(self):
        load_gpkg(self.outpath, group_name="DIAGNOSTIC")
        DiagnosticService._create_relations()
        return None

    def accept(self):
        try:
            self.merge_files()
            self.load()
            
            QMessageBox.information(self, "Succès",  f"Géopackage(s) compilé(s) et extrait(s) dans :\n{self.outpath}")
            super().accept()
            return

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")