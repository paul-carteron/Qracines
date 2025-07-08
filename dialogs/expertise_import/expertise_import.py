from PyQt5.QtWidgets import QMessageBox, QDialog, QFileDialog
from .expertise_import_dialog import Ui_ExpertiseImportDialog
from qgis.utils import iface
from qgis.core import QgsVectorLayer, QgsProcessing, QgsProject

# Import from utils folder
from ...utils.layer_utils import get_path, load_gpkg
from ...utils.custom_processing import calculate_essence_id, merge_with_ess
from ...core.layer_factory import LayerFactory

import processing
import pandas as pd

class ExpertiseImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = QgsProject.instance()
        self.iface = iface
        self.ui = Ui_ExpertiseImportDialog()  
        self.ui.setupUi(self)
        
        self.ui.pb_import_files.clicked.connect(self.import_files)
        
        # --- connect buttons ---
        self.ui.buttonBox.accepted.connect(self._on_accept)
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
        processing.run("native:package", {
            'LAYERS':      merged_layers,
            'OUTPUT':      str(out_path),
            'OVERWRITE':   True,
            'SAVE_STYLES': False
        })

        expertise_gpkg_path = get_path("expertise")
        load_gpkg(expertise_gpkg_path, group_name="EXPERTISE")

    def format_tra(self):

        tra_with_ess_id = processing.run("qgis:fieldcalculator", {
            'INPUT': self.tra,
            'FIELD_NAME': 'ESSENCE_ID',
            'FIELD_TYPE': 1,
            'FIELD_LENGTH': 50,
            'FIELD_PRECISION': 0,
            'FORMULA': """
                to_int(
                    coalesce(
                        nullif("TR_ESSENCE_ID", ''),
                        nullif("TR_ESSENCE_SECONDAIRE_ID", '')
                    )
                )
            """,
            'OUTPUT': 'memory:'
        })['OUTPUT']

        tra_with_ess = processing.run("qgis:joinattributestable", {
            'INPUT': tra_with_ess_id,
            'FIELD': 'ESSENCE_ID',
            'INPUT_2': self.ess,
            'FIELD_2': 'fid',
            'FIELDS_TO_COPY': ['essence', 'code', 'variation', 'type'],  # adjust if field names differ
            'METHOD': 1,  # Take only matching
            'DISCARD_NONMATCHING': False,
            'PREFIX': '',
            'OUTPUT': 'memory:'
        })['OUTPUT']

        formated_tra = processing.run("qgis:refactorfields", {
            'INPUT': tra_with_ess,
            'FIELDS_MAPPING': [
                {'expression': '"TR_STRATE"',    'name': 'STRATE',    'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"TR_PARCELLE"',  'name': 'PARCELLE',  'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"code"',         'name': 'CODE',      'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"essence"',      'name': 'ESSENCE',   'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"variation"',    'name': 'VARIATION', 'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"type"',         'name': 'TYPE',      'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"TR_DIAMETRE"',  'name': 'DIAMETRE',  'type': 2,  'length': 10, 'precision': 3},
                {'expression': '"TR_EFFECTIF"',  'name': 'EFFECTIF',  'type': 2,  'length': 10, 'precision': 0},
                {'expression': '"TR_HAUTEUR"',   'name': 'HAUTEUR',   'type': 2,  'length': 10, 'precision': 3},
            ],
            'OUTPUT': 'memory:'
        })['OUTPUT']

        formated_tra.setName("transect")

        return formated_tra

    def format_gha(self):

        gha_with_ess_id = calculate_essence_id(self.gha, "GHA_ESSENCE_ID", "GHA_ESSENCE_SECONDAIRE_ID")
        gha_with_ess = merge_with_ess(gha_with_ess_id, self.ess)
        
        gha_with_pla = processing.run("qgis:joinattributestable", {
            'INPUT': gha_with_ess,
            'FIELD': 'UUID',
            'INPUT_2': self.pla,
            'FIELD_2': 'UUID',
            'FIELDS_TO_COPY': ['fid', "PLTM_PARCELLE", "PLTM_STRATE", "PLTM_TYPE"],  # adjust if field names differ
            'METHOD': 1,  # Take only matching
            'DISCARD_NONMATCHING': False,
            'PREFIX': '',
            'OUTPUT': 'memory:'
        })['OUTPUT']

        formated_gha = processing.run("qgis:refactorfields", {
            'INPUT': gha_with_pla,
            'FIELDS_MAPPING': [
                {'expression': '"fid_2"',          'name': 'PLACETTE',    'type': 2,  'length': 50, 'precision': 0},
                {'expression': '"PLTM_STRATE"',    'name': 'STRATE',      'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"PLTM_PARCELLE"',  'name': 'PARCELLE',    'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"PLTM_TYPE"',      'name': 'PEUPLEMENT',  'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"GHA_G"',          'name': 'G',           'type': 2,  'length': 50, 'precision': 0},
                {'expression': '"code"',           'name': 'CODE',      'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"essence"',        'name': 'ESSENCE',   'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"variation"',      'name': 'VARIATION', 'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"type"',           'name': 'TYPE',      'type': 10, 'length': 50, 'precision': 0},
            ],
            'OUTPUT': 'memory:'
        })['OUTPUT']

        formated_gha.setName("gha")

        return formated_gha

    def format_va(self):

        va_with_ess_id = calculate_essence_id(self.va, "VA_ESSENCE_ID", "VA_ESSENCE_SECONDAIRE_ID")
        va_with_ess = merge_with_ess(va_with_ess_id, self.ess)
        
        va_with_pla = processing.run("qgis:joinattributestable", {
            'INPUT': va_with_ess,
            'FIELD': 'UUID',
            'INPUT_2': self.pla,
            'FIELD_2': 'UUID',
            'FIELDS_TO_COPY': ['fid', "PLTM_PARCELLE", "PLTM_STRATE", "PLTM_TYPE", "VA_TX_TROUEE"],  # adjust if field names differ
            'METHOD': 1,  # Take only matching
            'DISCARD_NONMATCHING': False,
            'PREFIX': '',
            'OUTPUT': 'memory:'
        })['OUTPUT']

        formated_va = processing.run("qgis:refactorfields", {
            'INPUT': va_with_pla,
            'FIELDS_MAPPING': [
                {'expression': '"fid_2"',          'name': 'PLACETTE',      'type': 2,  'length': 50, 'precision': 0},
                {'expression': '"PLTM_STRATE"',    'name': 'STRATE',        'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"PLTM_PARCELLE"',  'name': 'PARCELLE',      'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"PLTM_TYPE"',      'name': 'PEUPLEMENT',    'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"code"',           'name': 'CODE',          'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"essence"',        'name': 'ESSENCE',       'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"variation"',      'name': 'VARIATION',     'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"type"',           'name': 'TYPE',          'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"VA_TX_TROUEE"',   'name': 'TX_TROUEE',     'type': 2,  'length': 50, 'precision': 0},
                {'expression': '"VA_AGE_APP"',     'name': 'AGE',           'type': 2,  'length': 50, 'precision': 0},
                {'expression': '"VA_TX_HA"',       'name': 'RECOUVREMENT',  'type': 2,  'length': 50, 'precision': 0},
                {'expression': '"CUMUL_TX_VA"',    'name': 'CUMUL',         'type': 2, ' length': 50, 'precision': 0},
            ],
            'OUTPUT': 'memory:'
        })['OUTPUT']

        formated_va.setName("va")

        return formated_va
    
    def format_tse(self):

        tse_with_ess_id = calculate_essence_id(self.tse, "TSE_ESSENCE_ID", "TSE_ESSENCE_SECONDAIRE_ID")
        tse_with_ess = merge_with_ess(tse_with_ess_id, self.ess)
        
        tse_with_pla = processing.run("qgis:joinattributestable", {
            'INPUT': tse_with_ess,
            'FIELD': 'UUID',
            'INPUT_2': self.pla,
            'FIELD_2': 'UUID',
            'FIELDS_TO_COPY': ['fid', "PLTM_PARCELLE", "PLTM_STRATE", "PLTM_TYPE", "TSE_STERE_HA"],  # adjust if field names differ
            'METHOD': 1,  # Take only matching
            'DISCARD_NONMATCHING': False,
            'PREFIX': '',
            'OUTPUT': 'memory:'
        })['OUTPUT']

        formated_tse = processing.run("qgis:refactorfields", {
            'INPUT': tse_with_pla,
            'FIELDS_MAPPING': [
                {'expression': '"fid_2"',          'name': 'PLACETTE',      'type': 2,   'length': 50, 'precision': 0},
                {'expression': '"PLTM_STRATE"',    'name': 'STRATE',        'type': 10,  'length': 50, 'precision': 0},
                {'expression': '"PLTM_PARCELLE"',  'name': 'PARCELLE',      'type': 10,  'length': 50, 'precision': 0},
                {'expression': '"PLTM_TYPE"',      'name': 'PEUPLEMENT',    'type': 10,  'length': 50, 'precision': 0},
                {'expression': '"TSE_STERE_HA"',   'name': 'STERE_HA',      'type': 2,   'length': 50, 'precision': 0},
                {'expression': '"code"',           'name': 'CODE',          'type': 10,  'length': 50, 'precision': 0},
                {'expression': '"essence"',        'name': 'ESSENCE',       'type': 10,  'length': 50, 'precision': 0},
                {'expression': '"variation"',      'name': 'VARIATION',     'type': 10,  'length': 50, 'precision': 0},
                {'expression': '"type"',           'name': 'TYPE',          'type': 10,  'length': 50, 'precision': 0},
            ],
            'OUTPUT': 'memory:'
        })['OUTPUT']

        formated_tse.setName("tse")

        return formated_tse

    def format_reg(self):

        reg_with_ess_id = calculate_essence_id(self.reg, "REG_ESSENCE_ID", "REG_ESSENCE_SECONDAIRE_ID")
        reg_with_ess = merge_with_ess(reg_with_ess_id, self.ess)
        
        reg_with_pla = processing.run("qgis:joinattributestable", {
            'INPUT': reg_with_ess,
            'FIELD': 'UUID',
            'INPUT_2': self.pla,
            'FIELD_2': 'UUID',
            'FIELDS_TO_COPY': ['fid', "PLTM_PARCELLE", "PLTM_STRATE", "PLTM_TYPE"],  # adjust if field names differ
            'METHOD': 1,  # Take only matching
            'DISCARD_NONMATCHING': False,
            'PREFIX': '',
            'OUTPUT': 'memory:'
        })['OUTPUT']

        formated_reg = processing.run("qgis:refactorfields", {
            'INPUT': reg_with_pla,
            'FIELDS_MAPPING': [
                {'expression': '"fid_2"',          'name': 'PLACETTE',      'type': 2,   'length': 50, 'precision': 0},
                {'expression': '"PLTM_STRATE"',    'name': 'STRATE',        'type': 10,  'length': 50, 'precision': 0},
                {'expression': '"PLTM_PARCELLE"',  'name': 'PARCELLE',      'type': 10,  'length': 50, 'precision': 0},
                {'expression': '"PLTM_TYPE"',      'name': 'PEUPLEMENT',    'type': 10,  'length': 50, 'precision': 0},
                {'expression': '"REG_STADE"',      'name': 'TX_TROUEE',     'type': 10,  'length': 50, 'precision': 0},
                {'expression': '"REG_ETAT"',       'name': 'AGE',           'type': 10,  'length': 50, 'precision': 0},
                {'expression': '"code"',           'name': 'CODE',          'type': 10,  'length': 50, 'precision': 0},
                {'expression': '"essence"',        'name': 'ESSENCE',       'type': 10,  'length': 50, 'precision': 0},
                {'expression': '"variation"',      'name': 'VARIATION',     'type': 10,  'length': 50, 'precision': 0},
                {'expression': '"type"',           'name': 'TYPE',          'type': 10,  'length': 50, 'precision': 0},
            ],
            'OUTPUT': 'memory:'
        })['OUTPUT']

        formated_reg.setName("reg")

        return formated_reg

    @staticmethod
    def save_as_xlsx(*layers, path):

        processing.run("native:exporttospreadsheet", {
            'LAYERS': list(layers),
            'OUTPUT': str(path),
            'USE_ALIAS': False,
            'FORMATTED_VALUES': False,
            'OVERWRITE': True
        })

    def _on_accept(self):
        try:
            self.merge_files()

            self.ess = self.project.instance().mapLayersByName('essences')[0]
            self.pla = self.project.mapLayersByName('placette')[0]
            
            self.tra = self.project.mapLayersByName('transect')[0]
            self.gha = self.project.mapLayersByName('gha')[0]
            self.va = self.project.mapLayersByName('va')[0]
            self.tse = self.project.mapLayersByName('tse')[0]
            self.reg = self.project.mapLayersByName('reg')[0]

            formated_tra = self.format_tra()
            formated_gha = self.format_gha()
            formated_va = self.format_va()
            formated_tse = self.format_tse()
            formated_reg = self.format_reg()

            out_path = get_path("expertise_synthese")
            self.save_as_xlsx(formated_tra, formated_gha, formated_va, formated_tse, formated_reg, path = out_path)
            
            QMessageBox.information(self, "Succès",  f"Géopackage(s) compilé(s) et extrait(s) dans :\n{out_path}")
            return

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")