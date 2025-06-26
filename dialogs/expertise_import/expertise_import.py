from PyQt5.QtWidgets import QMessageBox, QDialog, QFileDialog
from .expertise_import_dialog import Ui_ExpertiseImportDialog
from qgis.utils import iface
from qgis.core import QgsVectorLayer, QgsProject, QgsProcessing

# Import from utils folder
from ...utils.variable_utils import get_global_variable, get_project_variable, get_project_variable
from ...utils.layer_utils import * 
from ...core.layer_factory import LayerFactory

import processing

class ExpertiseImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.ui = Ui_ExpertiseImportDialog()  
        self.ui.setupUi(self)
        
        self.ui.pb_import_files.clicked.connect(self.import_files)
        
        # --- connect buttons ---
        self.ui.buttonBox.accepted.connect(self.merge_files)
        self.ui.buttonBox.rejected.connect(self.reject)

    def import_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Sélectionner des fichiers à importer",
            "",  # starting directory
            "GeoPackage (*.gpkg)"
        )
        if files:
            self.ui.lw_selected_files.addItems(files)

    def merge_files(self):
        gpkgs = [self.ui.lw_selected_files.item(i).text() for i in range(self.ui.lw_selected_files.count())]
        if not gpkgs:
            QMessageBox.warning(self, "No files", "Aucun GeoPackage sélectionné.")
            return

        out_path = get_path("expertise")
        layers = LayerFactory.get_layer_names("EXPERTISE")

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

        print(merged_layers)
        processing.run("native:package", {
            'LAYERS':      merged_layers,
            'OUTPUT':      str(out_path),
            'OVERWRITE':   True,
            'SAVE_STYLES': False
        })

        
