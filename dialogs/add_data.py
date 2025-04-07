from PyQt5.QtWidgets import QDialog, QFileDialog
from .add_data_dialog import Ui_AddDataDialog
from qgis.core import QgsSettings

# Import from utils folder
from ..utils.variable_utils import *
from ..utils.layer_utils import *

class AddDataDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.ui = Ui_AddDataDialog()
        self.ui.setupUi(self)
        
        self.ui.buttonBox.clicked.connect(self.add_data_selected)
        
    def check_variables(self):
        styles_directory = get_global_variable("styles_directory")
        forest_directory = get_project_variable("forest_directory")
        forest_prefix = get_project_variable("forest_prefix")
        
        if not styles_directory or not forest_directory or not forest_prefix:
            self.iface.messageBar().pushMessage("Sequoia2", "Dossier Sequoia non paramêtrée", level=Qgis.Critical, duration=10)
            return False
        return True
        
    def add_data_selected(self):
        # Wms
            
        if self.ui.checkBox_SCAN25G.isChecked():
            server_names = ['Scan25_gray']
            import_wms_from_config(server_names, group_name="RASTER")
            replier()
            
        if self.ui.checkBox_SCAN25.isChecked():
            server_names = ['Scan25']
            import_wms_from_config(server_names, group_name="RASTER")
            replier()
            
        if self.ui.checkBox_SCAN100.isChecked():
            server_names = ['Scan100']
            import_wms_from_config(server_names, group_name="RASTER")
            replier()
        
        if self.ui.checkBox_SCAN1000.isChecked():
            server_names = ['Scan1000']
            import_wms_from_config(server_names, group_name="RASTER")
            replier()
            
        if self.ui.checkBox_IRCW.isChecked():
            server_names = ['IRC']
            import_wms_from_config(server_names, group_name="RASTER")
            replier()
            
        if self.ui.checkBox_RGBW.isChecked():
            server_names = ['RGB']
            import_wms_from_config(server_names, group_name="RASTER")
            replier()
            
        if self.ui.checkBox_SPOT.isChecked():
            server_names = ['SPOT']
            import_wms_from_config(server_names, group_name="RASTER")
            replier()
            
        if self.ui.checkBox_00.isChecked():
            server_names = ['00']
            import_wms_from_config(server_names, group_name="RASTER")
            replier()
            
        if self.ui.checkBox_06.isChecked():
            server_names = ['06']
            import_wms_from_config(server_names, group_name="RASTER")
            replier()
            
        if self.ui.checkBox_11.isChecked():
            server_names = ['11']
            import_wms_from_config(server_names, group_name="RASTER")
            replier()
            
        if self.ui.checkBox_50.isChecked():
            server_names = ['50']
            import_wms_from_config(server_names, group_name="RASTER")
            replier()
            
            
        if self.ui.checkBox_65.isChecked():
            server_names = ['65']
            import_wms_from_config(server_names, group_name="RASTER")
            replier()
            
        if self.ui.checkBox_80.isChecked():
            server_names = ['80']
            import_wms_from_config(server_names, group_name="RASTER")
            replier()
            
        if self.ui.checkBox_PCI.isChecked():
            server_names = ['PCI']
            import_wms_from_config(server_names, group_name="RASTER")
            replier()
            
        if self.ui.checkBox_GEOL.isChecked():
            server_names = ['GEOL']
            import_wms_from_config(server_names, group_name="RASTER")
            replier()
      
        
        # Vérification Vecteur + Raster
        if not self.check_variables():
            return
          
        styles_directory = get_global_variable("styles_directory")
        forest_directory = get_project_variable("forest_directory")
        forest_prefix = get_project_variable("forest_prefix")
        
        # Vecteur
        
        if self.ui.checkBox_UA.isChecked():
            vector_layers = ['UA_polygon_AME', 'UA_polygon_OCCUP', 'UA_polygon_PLT', 'UA_polygon']
            import_vectors_from_config(styles_directory, forest_directory, "new_directories", forest_prefix, vector_layers)
            replier()
        
        if self.ui.checkBox_SSPF.isChecked():
            vector_layers = ['SSPF_polygon', 'SSPF_line']
            import_vectors_from_config(styles_directory, forest_directory, "new_directories", forest_prefix, vector_layers)
            replier()
            
        if self.ui.checkBox_PF.isChecked():
            vector_layers = ['PF_polygon', 'PF_line']
            import_vectors_from_config(styles_directory, forest_directory, "new_directories", forest_prefix, vector_layers)
            replier()
        
        if self.ui.checkBox_ROUTE.isChecked():
            vector_layers = ['ROUTE_polygon', 'ROUTE_line']
            import_vectors_from_config(styles_directory, forest_directory, "new_directories", forest_prefix, vector_layers)
            replier()
        
        if self.ui.checkBox_TOPO.isChecked():
            vector_layers = ['TOPO_line']
            import_vectors_from_config(styles_directory, forest_directory, "new_directories", forest_prefix, vector_layers)
            replier()
            
        # Raster    
            
        if self.ui.checkBox_MNT.isChecked():
            raster_layers = ['MNT']
            import_rasters_from_config(styles_directory, forest_directory, "new_directories", forest_prefix, raster_layers, "RASTER")
            replier()
            
        if self.ui.checkBox_MNH.isChecked():
            raster_layers = ['MNH']
            import_rasters_from_config(styles_directory, forest_directory, "new_directories", forest_prefix, raster_layers, "RASTER")
            replier()  
            
        if self.ui.checkBox_RGB.isChecked():
            raster_layers = ['RGB']
            import_rasters_from_config(styles_directory, forest_directory, "new_directories", forest_prefix, raster_layers, "RASTER")
            replier() 
            
        if self.ui.checkBox_IRC.isChecked():
            raster_layers = ['IRC']
            import_rasters_from_config(styles_directory, forest_directory, "new_directories", forest_prefix, raster_layers, "RASTER")
            replier() 
            
        if self.ui.checkBox_PLTANC.isChecked():
            raster_layers = ['PLT-ANC']
            import_rasters_from_config(styles_directory, forest_directory, "new_directories", forest_prefix, raster_layers, "RASTER")
            replier()
            
        if self.ui.checkBox_PLT.isChecked():
            raster_layers = ['PLT']
            import_rasters_from_config(styles_directory, forest_directory, "new_directories", forest_prefix, raster_layers, "RASTER")
            replier()  
            
