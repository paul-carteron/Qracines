from PyQt5.QtWidgets import QDialog, QMessageBox
from Qracines.utils.message import messageLog
from qgis.PyQt import uic
from qgis.core import QgsProject, QgsCoordinateReferenceSystem
from qgis.utils import iface
from PyQt5.QtCore import QTimer

from .tree_marking_create_service import TreeMarkingCreateService

from ....core.db.manager import DatabaseManager

from ....utils.config import get_racines_path
from ....utils.ui import SeqLayerSelector, SpeciesSelector, QfieldPackager, DendroController
from ....utils.variable import get_project_variable, get_global_variable
from ....utils.essence import load_essences

from pathlib import Path
FORM_CLASS, _ = uic.loadUiType(
    Path(__file__).parent / "tree_marking_create.ui"
)

class TreeMarkingCreateDialog(QDialog, FORM_CLASS):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.iface = iface

        self.seq_id = get_project_variable("QS2_seq_id") or None
        self.seq_dir = get_project_variable("QS2_seq_dir") or None
        self.style_dir = get_global_variable("QS2_styles_directory") or None
        
        self.essences = load_essences(name = "Essences")
        
        self.dendro_controller = DendroController(
            self,
            dendro_spinbox={
                'dmin': 'sp_dmin',
                'dmax': 'sp_dmax',
                'hmin': 'sp_hmin',
                'hmax': 'sp_hmax'
            }
        )

        self.seq_vect_selector = SeqLayerSelector(
            ui = self,
            seq_dir = self.seq_dir,
            choices="lw_seq_vect", selected="lw_selected_seq_vect",
            add="pb_add_seq_vect", remove="pb_remove_seq_vect",
            filter="le_filter_seq_vect",
            type = "vect"
        )

        self.seq_rast_selector = SeqLayerSelector(
            ui = self,
            seq_dir = self.seq_dir,
            choices="lw_seq_rast", selected="lw_selected_seq_rast",
            add="pb_add_seq_rast", remove="pb_remove_seq_rast",
            filter="le_filter_seq_rast",
            type = "rast",
            default_keys = [
                "r.seq.plt", "r.ortho.irc", "r.alt.mnh.lidar", "r.alt.mnh.rge", "r.alt.ombrage.mnh"
            ]
        )

        self.ess_selector = SpeciesSelector(
            ui = self, layer = self.essences,
            choices="lw_species", selected="lw_selected_species",
            add="pb_add_species", remove="pb_remove_species",
            filter="le_filter_species"
        )

        self.packager = QfieldPackager(
            self,
            default_dir = get_racines_path("expertise", "Qfield", "Inventaire"),
            package_ui = 'cb_package_for_qfield',
            outdir_ui = 'fw_outdir'
            )

    def accept(self):
        if not self.ess_selector.is_valid():
            return

        self.iface.actionNewProject().trigger()
        QTimer.singleShot(0, lambda: QgsProject.instance().setCrs(
            QgsCoordinateReferenceSystem("EPSG:2154")
        ))

        codes = self.ess_selector.selected_codes()
        # 2) call service
        svc = TreeMarkingCreateService(
            seq_id = self.seq_id,
            seq_dir = self.seq_dir,
            style_dir = self.style_dir,
            seq_vect_keys = self.seq_vect_selector.selected_keys(),
            seq_rast_keys = self.seq_rast_selector.selected_keys(),
            codes=codes,
            dendro_controller = self.dendro_controller
        )

        try:
            svc.run()

            msg = "Inventaire complet !"
            if self.packager.is_valid():
                packaged_dir = self.packager.package(prefix="INV", seq_id=self.seq_id, codes=codes)
                msg += f"\nProjet packagé dans :\n{packaged_dir}"
            QMessageBox.information(self, "Succès", msg)

            super().accept()

        except Exception as e:
            # everything else bubbles up here
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue :\n{e}")
