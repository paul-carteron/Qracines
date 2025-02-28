from PyQt5.QtWidgets import QDialog, QFileDialog
from .diagnostic_dialog import Ui_DiagnosticDialog
from qgis.core import QgsSettings

class DiagnosticDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_DiagnosticDialog()
        self.ui.setupUi(self)
