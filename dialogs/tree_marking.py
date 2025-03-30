from PyQt5.QtWidgets import QDialog, QFileDialog
from .tree_marking_dialog import Ui_Tree_markingDialog
from qgis.core import QgsSettings

class Tree_markingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Tree_markingDialog()
        self.ui.setupUi(self)
