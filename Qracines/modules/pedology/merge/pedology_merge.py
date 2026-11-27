from pathlib import Path

from Qracines.utils.message import messageLog
from Qracines.utils.processing import save_as_xlsx
import processing
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox
from qgis.PyQt import uic
from qgis.core import QgsProcessing, QgsProject, QgsVectorLayer
from qgis.utils import iface

from ....utils.config import get_guides, get_qfield_path, get_stations
from ....utils.layers import create_relation
from ....utils.ui import GpkgLoader
from ..configurators.horizons import HorizonsConfigurator
from ..configurators.sondage import SondageConfigurator
from ..layer_schema import PEDOLOGY_LAYERS


FORM_CLASS, _ = uic.loadUiType(Path(__file__).parent / "pedology_merge.ui")


class PedologyMergeDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.project = QgsProject.instance()
        self.iface = iface

        self.gpkg_loader = GpkgLoader(ui=self, add="pb_import_files", selected="lw_selected_files",)

    @staticmethod
    def _all_stations():
        return list(
            dict.fromkeys(
                station
                for guide in get_guides()
                for station in get_stations(guide)
            )
        )

    def merge_files(self):
        gpkgs = self.gpkg_loader.selected_files
        merged_layers = {}

        for name in PEDOLOGY_LAYERS:
            source_layers = []
            for gpkg in gpkgs:
                layer = QgsVectorLayer(f"{gpkg}|layername={name}", name, "ogr")
                if layer.isValid():
                    source_layers.append(layer)

            if not source_layers:
                raise RuntimeError(f"La couche obligatoire '{name}' est absente des fichiers sélectionnés.")

            merged = processing.run("native:mergevectorlayers", {
                "LAYERS": source_layers,
                "CRS": "PROJECT",
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },)["OUTPUT"]

            if merged.fields().indexFromName("fid") != -1:
                merged = processing.run("qgis:deletecolumn", {
                    'INPUT':  merged,
                    'COLUMN': ['fid'],
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                })['OUTPUT']

            merged.setName(name)
            merged_layers[name] = merged

        return merged_layers

    def _configure_layers(self, layers):
        SondageConfigurator(layers["sondage"], self._all_stations()).configure()
        HorizonsConfigurator(layers["horizons"]).configure()


    def accept(self):
        if not self.gpkg_loader.is_valid():
            return

        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            QApplication.processEvents()
            relation = None
            relation_layers = []
            project_was_dirty = self.project.isDirty()
            try:
                gpkg_path = get_qfield_path("pedology")
                messageLog(f"gpkg_path: {gpkg_path}")
                merged_layers = self.merge_files()

                relation_layers = [
                    merged_layers["sondage"], merged_layers["horizons"]
                ]
                self.project.addMapLayers(relation_layers, False)
                relation = create_relation(
                    merged_layers["sondage"],
                    merged_layers["horizons"],
                    "UUID",
                    "SONDAGE",
                )
                flattened_layer = processing.run("native:flattenrelationships", {
                    "INPUT": merged_layers["sondage"],
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                })["OUTPUT"]
                flattened_layer.setName("sondage_horizons")

                processing.run("native:package", {
                    'LAYERS':      [*merged_layers.values(), flattened_layer],
                    'OUTPUT':      str(gpkg_path),
                    'OVERWRITE':   True,
                    'SAVE_STYLES': True
                })

                xlsx_path = get_qfield_path("pedology_synthese")
                save_as_xlsx(*merged_layers.values(), path=xlsx_path)
            finally:
                if relation is not None:
                    self.project.relationManager().removeRelation(relation.id())
                if relation_layers:
                    self.project.removeMapLayers(
                        [layer.id() for layer in relation_layers]
                    )
                self.project.setDirty(project_was_dirty)
                QApplication.restoreOverrideCursor()

            QMessageBox.information(self, "Succès",  f"Géopackage(s) compilé(s) et extrait(s) dans :\n{gpkg_path}")
            super().accept()

        except Exception as exc:
            QMessageBox.critical(
                self, "Erreur", f"Une erreur est survenue :\n{exc}"
            )
