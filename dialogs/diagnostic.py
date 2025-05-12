from pathlib import Path
from PyQt5.QtWidgets import QDialog, QMessageBox

from .diagnostic_dialog import Ui_DiagnosticDialog
from ..core.diagnostic_service import DiagnosticService
from ..utils.path_manager import get_project_variable, get_racines_path
from ..utils.variable_utils import clear_project

class DiagnosticDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_DiagnosticDialog()
        self.ui.setupUi(self)

        # --- initialise default output directory ---
        self.ui.le_forest_name.setText(get_project_variable("forest_prefix") or "Pas de forêt sélectionnée")

        # --- initialize raster checkboxes ---
        self.raster_checkboxes = {
            "plt_anc": self.ui.cb_plt_anc,
            "plt":     self.ui.cb_plt,
            "mnh":     self.ui.cb_mnh,
            "scan25":  self.ui.cb_scan25,
            "irc":     self.ui.cb_irc,
            "rgb":     self.ui.cb_rgb,
        }
        self.update_raster_checkbox_states()

        # --- initialise default output directory ---
        default_dir = Path(get_racines_path("expertise", "Diagnostic"))
        default_dir.mkdir(parents=True, exist_ok=True)
        self.ui.fw_package_outdir.setFilePath(str(default_dir))
        self.ui.fw_package_outdir.setStorageMode(self.ui.fw_package_outdir.GetDirectory)

        # --- connect buttons ---
        self.ui.buttonBox.accepted.connect(self._on_accept)
        self.ui.buttonBox.rejected.connect(self.reject)

         # --- connect checkbox to toggle ---
        self.setup_connections()

    def update_raster_checkbox_states(self):
        forest_selected = bool(get_project_variable("forest_prefix"))
        # These logical keys get auto-checked when a forest exists
        auto_check = {"plt_anc", "plt", "mnh", "scan25", "irc", "rgb"} if forest_selected else set()

        for logical_key, cb in self.raster_checkboxes.items():
            cb.setEnabled(forest_selected)
            cb.setChecked(logical_key in auto_check)

        self.ui.gb_diag_param.setEnabled(forest_selected)
        self.ui.gb_global_param.setEnabled(forest_selected)

    def setup_connections(self):
        self.ui.cb_package_for_qfield.toggled.connect(self.toggle_fw_editability)

    def toggle_fw_editability(self, checked):
        self.ui.fw_package_outdir.setEnabled(checked)
        self.ui.le_package_title.setEnabled(checked)

    def _on_accept(self):
        # 1) collect inputs
        outdir = Path(self.ui.fw_package_outdir.filePath())
        if not outdir.exists():
            QMessageBox.warning(self, "Invalid folder", "Please choose a valid directory.")
            return

        dmin, dmax = self.ui.sp_dmin.value(), self.ui.sp_dmax.value()
        hmin, hmax  = self.ui.sp_hmin.value(), self.ui.sp_hmax.value()
        
        clear_project()

        # 2) call service
        svc = DiagnosticService(
            outdir=outdir, title=self.ui.le_package_title.text(),
            package_for_qfield=self.ui.cb_package_for_qfield.isChecked(),
            dmin=dmin, dmax=dmax, hmin=hmin, hmax=hmax,
            raster_choices = self.raster_checkboxes
        ) 

        try:
            packaged_dir = svc.run_full_diagnostic()

            if packaged_dir:
                QMessageBox.information(self, "Succès", f"Diagnostic complet !\nProjet packagé dans :\n{packaged_dir}")
            else:
                QMessageBox.information(self, "Succès", "Diagnostic complet !")

            self.accept()

        except Exception as e:
            # everything else bubbles up here
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue :\n{e}")
