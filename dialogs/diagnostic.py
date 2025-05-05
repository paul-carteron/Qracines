from pathlib import Path
from PyQt5.QtWidgets import QDialog, QMessageBox

from .diagnostic_dialog import Ui_DiagnosticDialog
from ..core.diagnostic_service import DiagnosticService
from ..utils.path_manager import get_racines_path
from ..utils.variable_utils import create_new_projet_with_variables

class DiagnosticDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_DiagnosticDialog()
        self.ui.setupUi(self)

        # --- initialise default output directory ---
        default_dir = Path(get_racines_path("expertise", "Diagnostic"))
        default_dir.mkdir(parents=True, exist_ok=True)
        self.ui.exp_outdir.setFilePath(str(default_dir))
        self.ui.exp_outdir.setStorageMode(self.ui.exp_outdir.GetDirectory)
        self.ui.exp_outdir.setDialogTitle("Select output directory…")

        # --- connect buttons ---
        self.ui.buttonBox.accepted.connect(self._on_accept)
        self.ui.buttonBox.rejected.connect(self.reject)

    def _on_accept(self):
        # 1) collect inputs
        outdir = Path(self.ui.exp_outdir.filePath())
        if not outdir.exists():
            QMessageBox.warning(self, "Invalid folder", "Please choose a valid directory.")
            return

        dmin, dmax = self.ui.spinbox_dmin.value(), self.ui.spinbox_dmax.value()
        hmin, hmax  = self.ui.spinbox_hmin.value(), self.ui.spinbox_hmax.value()

        raster_choices = {
            "plt":       self.ui.checkbox_plt.isChecked(),
            "plt_anc":   self.ui.checkbox_plt_anc.isChecked(),
            "irc":       self.ui.checkbox_irc.isChecked(),
            "rgb":       self.ui.checkbox_rgb.isChecked(),
            "mnh":       self.ui.checkbox_mnh.isChecked(),
            "scan25":    self.ui.checkbox_scan25.isChecked(),
        }
        
        create_new_projet_with_variables()

        # 2) call service
        svc = DiagnosticService(
            output_dir=outdir,
            dmin=dmin, dmax=dmax, hmin=hmin, hmax=hmax,
            raster_choices=raster_choices
        )
        try:
            svc.run_full_diagnostic()
            QMessageBox.information(
                self, "Success",
                f"Diagnostic complete!\nPackaged project in:\n{outdir}"
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self, "Error running diagnostic",
                f"An error occurred:\n{e}"
            )
