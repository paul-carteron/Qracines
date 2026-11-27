from Qracines.utils.message import messageLog
from Qracines.utils.processing import calculate_essence_id, merge_with_ess, save_as_xlsx
import processing

from qgis.utils import iface
from qgis.core import QgsVectorLayer, QgsProcessing, QgsProject
from qgis.PyQt import uic
from PyQt5.QtWidgets import QMessageBox, QDialog

from ....utils.config import get_qfield_path
from ....utils.ui import GpkgLoader

from ..layer_schema import DIAGNOSTIC_LAYERS

from pathlib import Path

FORM_CLASS, _ = uic.loadUiType(
    Path(__file__).parent / "diagnostic_merge.ui")

class DiagnosticMergeDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.project = QgsProject.instance()
        self.iface = iface
        
        self.gpkg_loader = GpkgLoader(ui = self, add = 'pb_import_files', selected = 'lw_selected_files')

    def merge_files(self):
        if not self.gpkg_loader.is_valid():
            return {}
        gpkgs = self.gpkg_loader.selected_files

        layers = list(DIAGNOSTIC_LAYERS.keys())

        ess_layer_name = "Essences"
        ess_layer = QgsVectorLayer(f"{gpkgs[0]}|layername={ess_layer_name}", ess_layer_name, "ogr")

        merged_layers = {}
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
                'CRS':    self.project.crs(),
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            })['OUTPUT']
 
            # When merging, fid is reinitialized which mean duplicated fid that will cause geopackage creation to fail (processing.run("native:package"))
            merge_layer = processing.run("qgis:deletecolumn", {
                'INPUT':  merge_layer,
                'COLUMN': ['fid'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            })['OUTPUT']

            merge_layer.setName(layer)
            merged_layers[layer] = merge_layer

        merged_layers[ess_layer_name] = ess_layer

        return merged_layers

    def format_tra(self):

        tra_with_ess_id = calculate_essence_id(self.tra, "TR_ESS")
        tra_with_ess = merge_with_ess(tra_with_ess_id, self.ess)

        tr_diametre_expr = 'to_int("TR_DIAM")'
        tr_hauteur_expr = 'to_int("TR_HAUTEUR")'

        formated_tra = processing.run("qgis:refactorfields", {
            'INPUT': tra_with_ess,
            'FIELDS_MAPPING': [
                {'expression': '"TR_PARCELLE"',  'name': 'PARCELLE',  'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"code"',         'name': 'CODE',      'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"essence"',      'name': 'ESSENCE',   'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"variation"',    'name': 'VARIATION', 'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"type"',         'name': 'TYPE',      'type': 10, 'length': 50, 'precision': 0},
                {'expression': tr_diametre_expr,  'name': 'DIAMETRE',  'type': 2,  'length': 10, 'precision': 3},
                {'expression': '"TR_EFFECTIF"',  'name': 'EFFECTIF',  'type': 2,  'length': 10, 'precision': 0},
                {'expression': tr_hauteur_expr,   'name': 'HAUTEUR',   'type': 2,  'length': 10, 'precision': 3},
            ],
            'OUTPUT': 'memory:'
        })['OUTPUT']

        formated_tra.setName("transect")

        return formated_tra

    def format_gha(self):
        return self.format_placette_table(self.gha, "GHA_ESS", "gha", [
            {'expression': '"GHA_G"', 'name': 'G', 'type': 2, 'length': 50, 'precision': 0},
        ])

    def format_tse(self):
        return self.format_placette_table(self.tse, "TSE_ESS", "tse", [
            {'expression': '"TSE_DIM"', 'name': 'DIMENSION', 'type': 10, 'length': 50, 'precision': 0},
        ])

    def format_va(self):
        return self.format_placette_table(self.va, "VA_ESS", "va", [
            {'expression': '"VA_TX_HA"', 'name': 'TX_HA', 'type': 6, 'length': 50, 'precision': 3},
            {'expression': '"VA_CUMUL_TX_VA"', 'name': 'CUMUL_TX_VA', 'type': 6, 'length': 50, 'precision': 3},
        ])

    def format_reg(self):
        return self.format_placette_table(self.reg, "REG_ESS", "reg", [
            {'expression': '"REG_STADE"', 'name': 'STADE', 'type': 10, 'length': 50, 'precision': 0},
            {'expression': '"REG_ETAT"', 'name': 'ETAT', 'type': 10, 'length': 50, 'precision': 0},
        ])

    def format_placette_table(self, layer, essence_field, name, value_fields):
        layer_with_ess_id = calculate_essence_id(layer, essence_field)
        layer_with_ess = merge_with_ess(layer_with_ess_id, self.ess)
        
        layer_with_pla = processing.run("qgis:joinattributestable", {
            'INPUT': layer_with_ess,
            'FIELD': 'UUID',
            'INPUT_2': self.pla,
            'FIELD_2': 'UUID',
            'FIELDS_TO_COPY': ["COMPTEUR", "PLT_TYPE"],
            'METHOD': 1,  # Use the first matching placette without duplicating rows.
            'DISCARD_NONMATCHING': False,
            'PREFIX': 'pla_',
            'OUTPUT': 'memory:'
        })['OUTPUT']

        formated_layer = processing.run("qgis:refactorfields", {
            'INPUT': layer_with_pla,
            'FIELDS_MAPPING': [
                {'expression': '"pla_COMPTEUR"',   'name': 'PLACETTE',    'type': 2,  'length': 50, 'precision': 0},
                {'expression': '"pla_PLT_TYPE"',   'name': 'PEUPLEMENT',  'type': 10, 'length': 50, 'precision': 0},
                *value_fields,
                {'expression': '"code"',           'name': 'CODE',        'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"essence"',        'name': 'ESSENCE',     'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"variation"',      'name': 'VARIATION',   'type': 10, 'length': 50, 'precision': 0},
                {'expression': '"type"',           'name': 'TYPE',        'type': 10, 'length': 50, 'precision': 0},
            ],
            'OUTPUT': 'memory:'
        })['OUTPUT']

        formated_layer.setName(name)

        return formated_layer

    def accept(self):
        try:
            merged_layers = self.merge_files()
            if not merged_layers:
                return

            self.tra = merged_layers["Transect"]
            self.pla = merged_layers["Placette"]
            self.gha = merged_layers["Gha"]
            self.tse = merged_layers.get("Tse")
            self.va = merged_layers.get("Va")
            self.reg = merged_layers.get("Reg")
            self.ess = merged_layers["Essences"]

            formated_tra = self.format_tra()
            messageLog(f"formated_tra: {formated_tra}")
            
            formated_gha = self.format_gha()
            messageLog(f"formated_gha: {formated_gha}")

            synthesis_layers = [formated_tra, formated_gha]
            for layer, formatter in (
                (self.tse, self.format_tse),
                (self.va, self.format_va),
                (self.reg, self.format_reg),
            ):
                if layer is not None:
                    synthesis_layers.append(formatter())

            gpkg_path = get_qfield_path("diag")
            messageLog(f"gpkg_path: {gpkg_path}")

            processing.run("native:package", {
                'LAYERS':      list(merged_layers.values()),
                'OUTPUT':      str(gpkg_path),
                'OVERWRITE':   True,
                'SAVE_STYLES': True
            })

            xlsx_path = get_qfield_path("diag_synthese")
            save_as_xlsx(*synthesis_layers, path = xlsx_path)

            QMessageBox.information(self, "Succès",  f"Géopackage(s) compilé(s) et extrait(s) dans :\n{gpkg_path}")
            super().accept()
            return

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")
