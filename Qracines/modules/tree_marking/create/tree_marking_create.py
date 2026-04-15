from PyQt5.QtWidgets import QDialog, QMessageBox
from qgis.PyQt import uic
from qgis.core import QgsProject, QgsCoordinateReferenceSystem
from qgis.utils import iface
from PyQt5.QtCore import QTimer

from .tree_marking_create_service import TreeMarkingCreateService

from ....core.db.manager import DatabaseManager

from ....utils.config import get_racines_path
from ....utils.ui import RasterController, SpeciesSelector, QfieldPackager, DendroController
from ....utils.variable import get_project_variable

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
        
        self.essences = DatabaseManager().load_essences("Essences")
        
        self.dendro_controller = DendroController(
            self,
            dendro_spinbox={
                'dmin': 'sp_dmin',
                'dmax': 'sp_dmax',
                'hmin': 'sp_hmin',
                'hmax': 'sp_hmax'
            }
        )

        self.raster_controller = RasterController(
            ui=self,
            raster_checkbox={
                #   'key':     'checkbox_name',
                'r.seq.mnh': 'cb_plt',
                'r.alt.mnh': 'cb_mnh',
                'r.scan.25': 'cb_scan25',
                'r.ortho.irc': 'cb_irc',
                'r.ortho.rgb': 'cb_rgb',
            })

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
            codes=codes,
            dendro_controller = self.dendro_controller,
            raster_controller = self.raster_controller
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
