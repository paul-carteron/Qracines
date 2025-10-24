from pathlib import Path
from PyQt5.QtWidgets import QDialog, QMessageBox

from ...core.db.manager import DatabaseManager

from .diagnostic_create_dialog import Ui_DiagnosticDialog
from .diagnostic_create_service import DiagnosticService
from ...utils.config import get_racines_path
from ...utils.utils import clear_project
from ...utils.ui import RasterController, QfieldPackager, GridController


class DiagnosticDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_DiagnosticDialog()
        self.ui.setupUi(self)
        self.essences_layer = DatabaseManager().load_essences("Essences")

        raster_checkbox = {
            #   'key':     'checkbox_name',
                'plt_anc': 'cb_plt_anc',
                'plt':     'cb_plt',
                'mnh':     'cb_mnh',
                'scan25':  'cb_scan25',
                'irc':     'cb_irc'
            }
        self.raster_controller = RasterController(ui=self.ui, raster_checkbox=raster_checkbox)
        
        self.packager = QfieldPackager(
            self.ui,
            default_dir = get_racines_path("expertise", "Qfield", "Diagnostic"),
            package_ui = 'cb_package_for_qfield',
            outdir_ui = 'fw_outdir'
            )
        
        self.grid_controller = GridController(
            self.ui,
            create_grid_ui = 'cb_create_grid',
            points_per_ha_ui = 'dsp_points_per_ha'
        )

    def accept(self):

        clear_project()

        # 2) call service
        svc = DiagnosticService(
            dmin=self.ui.sp_dmin.value(),
            dmax=self.ui.sp_dmax.value(),
            hmin=self.ui.sp_hmin.value(),
            hmax=self.ui.sp_hmax.value(),
            essences_layer = self.essences_layer,
            grid_controller = self.grid_controller
        )

        try:
            svc.run()
            self.raster_controller.load_selected_rasters()

            msg = "Expertise complète !"
            if self.packager.is_valid():
                packaged_dir = self.packager.package(prefix="DIAG")
                msg += f"\nProjet packagé dans :\n{packaged_dir}"
            QMessageBox.information(self, "Succès", msg)

            super().accept()
        except Exception as e:
            # everything else bubbles up here
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue :\n{e}")
