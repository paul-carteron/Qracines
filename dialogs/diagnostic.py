from PyQt5.QtWidgets import *
from .diagnostic_dialog import Ui_DiagnosticDialog
from qgis.core import *

# Import from utils folder
from ..utils.variable_utils import *
from ..utils.layer_utils import *
from ..utils.qfield_utils import *

class DiagnosticDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_DiagnosticDialog()
        self.ui.setupUi(self)
        
        self.import_all_layers()
        self.create_gpkg()
        
    def import_all_layers(self):
        self.ui.progressBar.setValue(5)
        clear_qgis_project()
        styles_directory = get_global_variable("styles_directory")
        forest_directory = get_project_variable("forest_directory")
        forest_prefix = get_project_variable("forest_prefix")
        
        # Raster import
        self.ui.label.setText("Import des rasters ...")
        import_wms_from_config(['PLT','PLT-ANC','IRC','RGB','MNH','SCAN25'], group_name="RASTER")
        self.ui.progressBar.setValue(15)
        
        # Vector import
        self.ui.label.setText("Import des vecteurs ...")
        vector_layers = ['PROP_line', 'PROP-Diag_line', 'PF_line', 'PF-Diag_line', 'PF_polygon', 'SSPF_polygon', 'SSPF-Diag_polygon', 'UA_polygon']
        import_vectors_from_config(styles_directory, forest_directory, "new_directories", forest_prefix, vector_layers)
        replier()
        self.ui.progressBar.setValue(25)
        
    def create_gpkg(self):
        pass
