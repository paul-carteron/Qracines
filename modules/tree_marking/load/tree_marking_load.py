import processing

from qgis.utils import iface
from qgis.core import QgsVectorLayer, QgsProcessing, QgsProject, QgsMapLayer
from PyQt5.QtWidgets import QMessageBox, QDialog
from qgis.PyQt import uic

# Import from utils folder
from ....utils.layers import load_gpkg
from ....utils.processing import calculate_essence_id, merge_with_ess, save_as_xlsx
from ....utils.ui import GpkgLoader
from ....utils.config import get_new_to_old, get_qfield_path
from ....utils.message import messageLog
from ....utils.variable import get_project_variable

from ..config import TYPE_CHOICES, MARQUAGE_CHOICES, COULEUR_CHOICES, MARTEAU_CHOICES
from ..configurators.param import ParamConfigurator
from ..configurators.arbres import  ArbresConfigurator
from ..layer_schema import TREE_MARKING_LAYERS

from pathlib import Path
FORM_CLASS, _ = uic.loadUiType(
    Path(__file__).parent / "tree_marking_load.ui")

class TreeMarkingLoadDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.project = QgsProject.instance()
        self.iface = iface
        
        self.gpkg_loader = GpkgLoader(ui = self, add = 'pb_import_files', selected = 'lw_selected_files')

    def merge_files(self):
        if self.gpkg_loader.is_valid():
            gpkgs = self.gpkg_loader.selected_files

        layers = list(TREE_MARKING_LAYERS.keys())

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
                'LAYERS': all_layer, 
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
            merged_layers[layer] = merge_layer

        merged_layers[ess_layer_name] = ess_layer

        return merged_layers

    @staticmethod
    def build_qgis_map_expr(field, mapping):
        items = ", ".join(
                f"'{k.replace("'", "''")}','{v.replace("'", "''")}'"
                for k, v in mapping.items()
            )
        return f"coalesce(map({items})[\"{field}\"], \"{field}\")"

    def format_param(self):

        type_expr = self.build_qgis_map_expr("TYPE", TYPE_CHOICES)
        marquage_bo_expr = self.build_qgis_map_expr("MARQUAGE_BO", MARQUAGE_CHOICES)
        couleur_bo_expr = self.build_qgis_map_expr("COULEUR_BO", COULEUR_CHOICES)
        marquage_bi_expr = self.build_qgis_map_expr("MARQUAGE_BI", MARQUAGE_CHOICES)
        couleur_bi_expr = self.build_qgis_map_expr("COULEUR_BI", COULEUR_CHOICES)
        marteau_expr = self.build_qgis_map_expr("MARTEAU", MARTEAU_CHOICES)

        formated_param = processing.run("qgis:refactorfields", {
                'INPUT': self.param,
                'FIELDS_MAPPING': [
                    {'expression': '"PARCELLE"',    'name': 'PARCELLE',    'type': 10, 'length': 50, 'precision': 0},
                    {'expression': '"SURFACE"',     'name': 'SURFACE',     'type': 2,  'length': 10, 'precision': 4},
                    {'expression': '"LOT"',         'name': 'GROUPE',      'type': 10, 'length': 50, 'precision': 0},
                    {'expression': type_expr,        'name': 'TYPE',        'type': 10, 'length': 50, 'precision': 0},
                    {'expression': marquage_bo_expr, 'name': 'MARQUAGE_BO', 'type': 10, 'length': 50, 'precision': 0},
                    {'expression': couleur_bo_expr,  'name': 'COULEUR_BO',  'type': 10, 'length': 50, 'precision': 0},
                    {'expression': marquage_bi_expr, 'name': 'MARQUAGE_BI', 'type': 10, 'length': 50, 'precision': 0},
                    {'expression': couleur_bi_expr,  'name': 'COULEUR_BI',  'type': 10, 'length': 50, 'precision': 0},
                    {'expression': marteau_expr,      'name': 'MARQUE',      'type': 10, 'length': 50, 'precision': 0},
                ],
                'OUTPUT': 'memory:'
            })['OUTPUT']

        formated_param.setName("parcelles")

        return formated_param

    def format_arbres(self, for_invpap = True):

        arbres_with_ess_id = calculate_essence_id(self.arbres, "ESSENCE_ID", "ESSENCE_SECONDAIRE_ID")
        arbres_with_ess = merge_with_ess(arbres_with_ess_id, self.ess)

        if for_invpap:
            nto = get_new_to_old()

            mapping_items = ", ".join(
                f"'{k.replace("'", "''")}','{v.replace("'", "''")}'"
                for k, v in nto.items()
            )

            ess_expr = f"""
            coalesce(
                map({mapping_items})[
                    trim(concat("essence", ' ', "variation"))
                ],
                trim(concat("essence", ' ', "variation"))
            )
            """

            formated_arbres = processing.run("qgis:refactorfields", {
                'INPUT': arbres_with_ess,
                'FIELDS_MAPPING': [
                    {'expression': '"fid"',         'name': 'ID',         'type': 10, 'length': 50, 'precision': 0},
                    {'expression': '"PARCELLE"',    'name': 'PARCELLE',    'type': 10, 'length': 50, 'precision': 0},
                    {'expression': ess_expr,        'name': 'ESSENCE',     'type': 10, 'length': 50, 'precision': 0},
                    {'expression': '"DIAMETRE"',    'name': 'DIAMETRE',    'type': 2,  'length': 10, 'precision': 3},
                    {'expression': '"HAUTEUR"',     'name': 'HAUTEUR',     'type': 2,  'length': 10, 'precision': 3},
                    {'expression': '"OBSERVATION"', 'name': 'OBSERVATION', 'type': 10, 'length': 10, 'precision': 3},
                    {'expression': '"EFFECTIF"',    'name': 'EFFECTIF',    'type': 2,  'length': 10, 'precision': 0},
                    {'expression': '"LOT"',         'name': 'GROUPE',      'type': 10, 'length': 50, 'precision': 0},
                ],
                'OUTPUT': 'memory:'
            })['OUTPUT']

            formated_arbres.setName("arbres")

        else:
            formated_arbres = processing.run("qgis:refactorfields", {
                'INPUT': arbres_with_ess,
                'FIELDS_MAPPING': [
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

            formated_arbres.setName("transect")

        return formated_arbres

    def compute_ess_summary(self):

        ess_id = 'coalesce(nullif("ESSENCE_ID", \'\'), nullif("ESSENCE_SECONDAIRE_ID", \'\'))'

        ess_summary = processing.run(
            "native:aggregate",
            {
                'INPUT': self.arbres,
                'GROUP_BY': ess_id,
                'AGGREGATES': [
                    {
                        'aggregate': 'first_value',
                        'input': ess_id,
                        'name': 'ESSENCE_ID',
                        'type': 4,
                        'length': 0,
                        'precision': 0
                    },
                    {
                        'aggregate': 'sum',
                        'input': '"EFFECTIF"',
                        'name': 'NB',
                        'type': 4,
                        'length': 0,
                        'precision': 0
                    },
                    {
                        'aggregate': 'minimum',
                        'input': 'to_int("DIAMETRE")',
                        'name': 'MIN',
                        'type': 4,
                        'length': 0,
                        'precision': 0
                    },
                    {
                        'aggregate': 'maximum',
                        'input': 'to_int("DIAMETRE")',
                        'name': 'MAX',
                        'type': 4,
                        'length': 0,
                        'precision': 0
                    },
                ],
                'OUTPUT': 'TEMPORARY_OUTPUT'
            }
        )['OUTPUT']

        ess_summary = processing.run(
            "native:dropgeometries",
            {
                'INPUT': ess_summary,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            }
        )['OUTPUT']

        ess_summary.setName("ess_summary")

        return ess_summary

    def accept(self):
        try:
            merged_layers = self.merge_files()

            self.ess = merged_layers["Essences"]
            self.arbres = merged_layers["Arbres"]
            self.param = merged_layers["Param"]

            # Make layer private
            formated_arbres = self.format_arbres()
            formated_param = self.format_param()
            ess_summary = self.compute_ess_summary()

            merged_layers[ess_summary.name()] = ess_summary

            gpkg_path = get_qfield_path("inventaire")
            processing.run("native:package", {
                'LAYERS':      list(merged_layers.values()),
                'OUTPUT':      str(gpkg_path),
                'OVERWRITE':   True,
                'SAVE_STYLES': True
            })
            
            layers = load_gpkg(gpkg_path, group_name="INVENTAIRE")

            seq_id = get_project_variable("QS2_seq_id") or None
            ParamConfigurator(layers["Param"], seq_id=seq_id).configure()
            ArbresConfigurator(
                layers["Arbres"],
                layers["Param"],
                layers["Essences"],
                layers["lst_hauteur"],
                layers["lst_diam"]
            ).configure()
            layers["lst_hauteur"].setFlags(layers["lst_hauteur"].flags() | QgsMapLayer.Private)
            layers["lst_diam"].setFlags(layers["lst_diam"].flags() | QgsMapLayer.Private)

            self._save_style(layers)

            unique_ess = processing.run("qgis:listuniquevalues", {
                'INPUT': formated_arbres,
                'FIELDS':['ESSENCE'],
                'OUTPUT':'TEMPORARY_OUTPUT'
            })['OUTPUT']
            unique_ess.setName("essence")

            out_path = get_qfield_path("inventaire_synthese")
            save_as_xlsx(formated_param, unique_ess, formated_arbres, path = out_path)
            
            QMessageBox.information(self, "Succès",  f"Géopackage(s) compilé(s) et extrait(s) dans :\n{out_path}")
            
            super().accept()

            return
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")
    
    def _save_style(self, layers):

        for layer in layers.values():

            layer.saveStyleToDatabase(
                name="default",
                description="default",
                useAsDefault=True,
                uiFileContent=""
            )