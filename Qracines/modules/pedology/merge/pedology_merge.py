from pathlib import Path

import processing
from PyQt5.QtWidgets import QDialog, QMessageBox
from qgis.PyQt import uic
from qgis.core import QgsProcessing, QgsProject, QgsVectorLayer
from qgis.utils import iface

from ....utils.config import get_guides, get_qfield_path, get_stations
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

        self.gpkg_loader = GpkgLoader(
            ui=self,
            add="pb_import_files",
            selected="lw_selected_files",
        )

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
                raise RuntimeError(
                    f"La couche obligatoire '{name}' est absente des fichiers sélectionnés."
                )

            merged = processing.run(
                "native:mergevectorlayers",
                {
                    "LAYERS": source_layers,
                    "CRS": "PROJECT",
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
            )["OUTPUT"]

            if merged.fields().indexFromName("fid") != -1:
                merged = processing.run(
                    "qgis:deletecolumn",
                    {
                        "INPUT": merged,
                        "COLUMN": ["fid"],
                        "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                    },
                )["OUTPUT"]

            merged.setName(name)
            merged_layers[name] = merged

        self._configure_layers(merged_layers)

        output_path = get_qfield_path("pedology")
        result = processing.run(
            "native:package",
            {
                "LAYERS": list(merged_layers.values()),
                "OUTPUT": str(output_path),
                "OVERWRITE": True,
                "SAVE_STYLES": True,
                "EXPORT_RELATED_LAYERS": True,
            },
        )

        return result["OUTPUT"]

    def _configure_layers(self, layers):
        SondageConfigurator(
            layers["sondage"], self._all_stations()
        ).configure()
        HorizonsConfigurator(layers["horizons"]).configure()

    def accept(self):
        if not self.gpkg_loader.is_valid():
            return

        try:
            output_path = self.merge_files()
            QMessageBox.information(
                self,
                "Succès",
                f"Géopackage(s) compilé(s) dans :\n{output_path}",
            )
            super().accept()
        except Exception as exc:
            QMessageBox.critical(
                self, "Erreur", f"Une erreur est survenue :\n{exc}"
            )
