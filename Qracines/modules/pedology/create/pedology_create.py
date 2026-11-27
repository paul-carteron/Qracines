from pathlib import Path

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QDialog, QMessageBox
from qgis.PyQt import uic
from qgis.core import QgsCoordinateReferenceSystem, QgsProject
from qgis.utils import iface

from .pedology_create_service import PedologyCreateService
from ....utils.config import get_guide_label, get_guides, get_racines_path
from ....utils.ui import QfieldPackager, SeqLayerSelector
from ....utils.variable import get_global_variable, get_project_variable


FORM_CLASS, _ = uic.loadUiType(Path(__file__).parent / "pedology_create.ui")


class PedologyCreateDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.seq_dir = get_project_variable("QS2_seq_dir") or None
        self.seq_id = get_project_variable("QS2_seq_id") or None
        self.style_dir = get_global_variable("QS2_styles_directory") or None

        for guide in get_guides():
            self.cob_stations.addItem(get_guide_label(guide), guide)

        self.seq_vect_selector = SeqLayerSelector(
            ui=self,
            seq_dir=self.seq_dir,
            choices="lw_seq_vect",
            selected="lw_selected_seq_vect",
            add="pb_add_seq_vect",
            remove="pb_remove_seq_vect",
            filter="le_filter_seq_vect",
            type="vect",
            default_keys=["v.seq.ua.poly"],
        )

        self.seq_rast_selector = SeqLayerSelector(
            ui=self,
            seq_dir=self.seq_dir,
            choices="lw_seq_rast",
            selected="lw_selected_seq_rast",
            add="pb_add_seq_rast",
            remove="pb_remove_seq_rast",
            filter="le_filter_seq_rast",
            type="rast",
            default_keys=[
                "r.seq.plt",
                "r.ortho.irc",
                "r.alt.mnh.lidar",
                "r.alt.mnh.rge",
                "r.alt.ombrage.mnh",
            ],
        )

        self.packager = QfieldPackager(
            self,
            default_dir=get_racines_path("expertise", "Qfield", "Pedology"),
            package_ui="cb_package_for_qfield",
            outdir_ui="fw_outdir",
        )

    def accept(self):
        iface.actionNewProject().trigger()
        QTimer.singleShot(
            0,
            lambda: QgsProject.instance().setCrs(
                QgsCoordinateReferenceSystem("EPSG:2154")
            ),
        )

        service = PedologyCreateService(
            guide=self.cob_stations.currentData(),
            seq_dir=self.seq_dir,
            style_dir=self.style_dir,
            seq_vect_keys=self.seq_vect_selector.selected_keys(),
            seq_rast_keys=self.seq_rast_selector.selected_keys(),
        )

        try:
            service.run()

            message = "Projet pédologique terminé !"
            if self.packager.is_valid():
                packaged_dir = self.packager.package(
                    prefix="PEDO",
                    seq_id=self.seq_id,
                    assets=[
                        Path(__file__).parents[3]
                        / "assets"
                        / "triangle_des_textures.jpeg"
                    ],
                )
                message += f"\nProjet packagé dans :\n{packaged_dir}"

            QMessageBox.information(self, "Succès", message)
            super().accept()
        except Exception as exc:
            QMessageBox.critical(
                self, "Erreur", f"Une erreur est survenue :\n{exc}"
            )
