from PyQt5.QtWidgets import QDialog, QFileDialog
from .add_data_dialog import Ui_AddDataDialog
from qgis.core import QgsSettings

class AddDataDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_AddDataDialog()
        self.ui.setupUi(self)
