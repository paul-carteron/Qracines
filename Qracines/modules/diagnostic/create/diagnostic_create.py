from PyQt5.QtWidgets import QDialog, QMessageBox
from qgis.PyQt import uic
from qgis.core import QgsProject, QgsCoordinateReferenceSystem
from PyQt5.QtCore import QTimer
from qgis.utils import iface

from .diagnostic_create_service import DiagnosticCreateService
from ....utils.config import get_racines_path
from ....utils.ui import SeqLayerSelector, QfieldPackager, GridController, DendroController
from ....utils.variable import get_project_variable, get_global_variable

from pathlib import Path
FORM_CLASS, _ = uic.loadUiType(
    Path(__file__).parent / "diagnostic_create.ui"
)
  
class DiagnosticCreateDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.seq_dir = get_project_variable("QS2_seq_dir") or None
        self.seq_id = get_project_variable("QS2_seq_id") or None
        self.style_dir = get_global_variable("QS2_styles_directory") or None

        self.dendro_controller = DendroController(
            self,
            dendro_spinbox={
                'dmin': 'sp_dmin',
                'dmax': 'sp_dmax',
                'hmin': 'sp_hmin',
                'hmax': 'sp_hmax'
            }
        )

        self.grid_controller = GridController(
            self,
            create_grid_ui = 'cb_create_grid',
            points_per_ha_ui = 'dsp_points_per_ha'
        )

        self.seq_vect_selector = SeqLayerSelector(
            ui = self,
            seq_dir = self.seq_dir,
            choices="lw_seq_vect", selected="lw_selected_seq_vect",
            add="pb_add_seq_vect", remove="pb_remove_seq_vect",
            filter="le_filter_seq_vect",
            type = "vect",
            default_keys = [
                'v.seq.ua.poly',
                'v.infra.point', 'v.infra.line', 'v.infra.poly',
                'v.vege.line',
                'v.hydro.point', 'v.hydro.line', 'v.hydro.poly',
                'v.road.line'
            ]
        )

        self.seq_rast_selector = SeqLayerSelector(
            ui = self,
            seq_dir = self.seq_dir,
            choices="lw_seq_rast", selected="lw_selected_seq_rast",
            add="pb_add_seq_rast", remove="pb_remove_seq_rast",
            filter="le_filter_seq_rast",
            type = "rast",
            default_keys = [
                "r.seq.plt", "r.ortho.irc", "r.alt.mnh.lidar", "r.alt.mnh.rge", "r.alt.ombrage.mnh",
                "r.alt.mnh.lidar", "r.alt.mnt.rge"
            ]
        )
        
        self.packager = QfieldPackager(
            self,
            default_dir = get_racines_path("expertise", "Qfield", "Diagnostic"),
            package_ui = 'cb_package_for_qfield',
            outdir_ui = 'fw_outdir'
            )
        
    def accept(self):

        iface.actionNewProject().trigger()

        QTimer.singleShot(0, lambda: QgsProject.instance().setCrs(
            QgsCoordinateReferenceSystem("EPSG:2154")
        ))

        svc = DiagnosticCreateService(
            seq_dir = self.seq_dir,
            style_dir = self.style_dir,
            seq_vect_keys = self.seq_vect_selector.selected_keys(),
            seq_rast_keys = self.seq_rast_selector.selected_keys(),
            dendro_controller = self.dendro_controller,
            grid_controller = self.grid_controller,
        )

        try:
            svc.run()

            msg = "Diagnostic complète !"
            if self.packager.is_valid():
                packaged_dir = self.packager.package(prefix="DIAG", seq_id=self.seq_id)
                msg += f"\nProjet packagé dans :\n{packaged_dir}"
            QMessageBox.information(self, "Succès", msg)

            super().accept()
        except Exception as e:
            # everything else bubbles up here
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue :\n{e}")
