from PyQt5.QtWidgets import QDialog, QMessageBox

from .diagnostic_create_dialog import Ui_DiagnosticDialog
from .diagnostic_create_service import DiagnosticService
from .....utils.config import get_racines_path
from .....utils.utils import clear_project
from .....utils.ui import RasterController, QfieldPackager, GridController, DendroController

class DiagnosticDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_DiagnosticDialog()
        self.ui.setupUi(self)

        self.dendro_controller = DendroController(
            self.ui,
            dendro_spinbox={
                'dmin': 'sp_dmin',
                'dmax': 'sp_dmax',
                'hmin': 'sp_hmin',
                'hmax': 'sp_hmax'
            }
        )

        self.grid_controller = GridController(
            self.ui,
            create_grid_ui = 'cb_create_grid',
            points_per_ha_ui = 'dsp_points_per_ha'
        )

        self.raster_controller = RasterController(
            ui=self.ui,
            raster_checkbox={
                #   'key':     'checkbox_name',
                'plt':     'cb_plt',
                'plt_anc': 'cb_plt_anc',
                'mnh':     'cb_mnh',
                'mnt':     'cb_mnt',
                'scan25':  'cb_scan25',
                'irc':     'cb_irc'
            })
        
        self.packager = QfieldPackager(
            self.ui,
            default_dir = get_racines_path("expertise", "Qfield", "Diagnostic"),
            package_ui = 'cb_package_for_qfield',
            outdir_ui = 'fw_outdir'
            )
        
    def accept(self):

        clear_project()

        svc = DiagnosticService(
            dendro_controller = self.dendro_controller,
            grid_controller = self.grid_controller,
            raster_controller = self.raster_controller
        )

        try:
            svc.run()

            msg = "Diagnodtic complète !"
            if self.packager.is_valid():
                packaged_dir = self.packager.package(prefix="DIAG")
                msg += f"\nProjet packagé dans :\n{packaged_dir}"
            QMessageBox.information(self, "Succès", msg)

            super().accept()
        except Exception as e:
            # everything else bubbles up here
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue :\n{e}")
