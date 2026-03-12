import processing

from qgis.utils import iface
from qgis.core import QgsVectorLayer, QgsProcessing, QgsProject
from qgis.PyQt import uic
from PyQt5.QtWidgets import QMessageBox, QDialog

from ....utils.layers import get_path, load_gpkg
from ....utils.ui import GpkgLoader

from ....core.layer.factory import LayerFactory

from ..layer_schema import DIAGNOSTIC_LAYERS

from pathlib import Path
FORM_CLASS, _ = uic.loadUiType(
    Path(__file__).parent / "diagnostic_load.ui")

class DiagnosticLoadDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.project = QgsProject.instance()
        self.iface = iface
        
        self.gpkg_loader = GpkgLoader(ui = self, add = 'pb_import_files', selected = 'lw_selected_files')

    def merge_files(self):
        if self.gpkg_loader.is_valid():
            gpkgs = self.gpkg_loader.selected_files

        out_path = get_path("diag")
        layers = list(DIAGNOSTIC_LAYERS.keys())

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

    def accept(self):
        try:
            self.merge_files()
            self.load()
            
            QMessageBox.information(self, "Succès",  f"Géopackage(s) compilé(s) et extrait(s) dans :\n{self.outpath}")
            super().accept()
            return

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")