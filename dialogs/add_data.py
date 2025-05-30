from PyQt5.QtWidgets import QDialog, QFileDialog
from .add_data_dialog import Ui_AddDataDialog
from qgis.core import QgsSettings

# Import from utils folder
from ..utils.variable_utils import get_global_variable, get_project_variable, get_project_variable
from ..utils.layer_utils import *

class AddDataDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.ui = Ui_AddDataDialog()
        self.ui.setupUi(self)
        
        self.VECTOR_CHECKBOX_KEY_MAP = {
            self.ui.checkBox_ROUTE: ['route_polygon', 'route_line'],
            self.ui.checkBox_PF: ['pf_polygon', 'pf_line'],
            self.ui.checkBox_SSPF: ['sspf_polygon', 'sspf_line'],
            self.ui.checkBox_UA: ['ua_polygon_ame', 'ua_polygon_occup', 'ua_polygon_plt', 'ua_polygon'],
            self.ui.checkBox_TOPO: ['topo_line'],
        }

        self.RASTER_CHECKBOX_KEY_MAP = {
            self.ui.checkBox_PLT: "plt",
            self.ui.checkBox_PLTANC: "plt_anc",
            self.ui.checkBox_IRC: "irc",
            self.ui.checkBox_RGB: "rgb",
            self.ui.checkBox_MNH: "mnh",
            self.ui.checkBox_MNT: "mnt",
            self.ui.checkBox_SCAN: "scan25",
        }

        self.WMS_CHECKBOX_KEY_MAP = {
            # SCAN
            self.ui.checkBox_SCAN1000: "wms_scan1000",
            self.ui.checkBox_SCAN100: "wms_scan100",
            self.ui.checkBox_SCAN25: "wms_scan25",
            self.ui.checkBox_SCAN25G: "wms_scan25_grey",
            # ORTHO
            self.ui.checkBox_IRCW: "wms_irc",
            self.ui.checkBox_RGBW: "wms_rgb",
            self.ui.checkBox_SPOT: "wms_spot_2023",
            # ORTHOHISTO
            self.ui.checkBox_50: "wms_histo_1950",
            self.ui.checkBox_65: "wms_histo_1965",
            self.ui.checkBox_80: "wms_histo_1980",
            self.ui.checkBox_00: "wms_histo_2000", 
            self.ui.checkBox_06: "wms_histo_2006",
            self.ui.checkBox_11: "wms_histo_2011",
            # AUTRES
            self.ui.checkBox_GEOL: "wms_geol",
            self.ui.checkBox_PCI: "wms_pci",
        }

        self.ui.buttonBox.clicked.connect(self.add_data)
    
    def add_data(self):
        self._check_variables()
        self._add_vector()
        self._add_raster()
        self._add_wms()

    def _check_variables(self):
        styles_directory = get_global_variable("styles_directory")
        forest_directory = get_project_variable("forest_directory")
        forest_prefix = get_project_variable("forest_prefix")
        
        if not (styles_directory and forest_directory and forest_prefix):
            self.iface.messageBar().pushMessage("Sequoia2", "Dossier Sequoia non paramêtrée", level=Qgis.Critical, duration=10)
            return False
        return True
    
    def _add_vector(self):
        # flatten list of list
        vector_keys = [
            key
            for cb, key_list in self.VECTOR_CHECKBOX_KEY_MAP.items() if cb.isChecked()
            for key in key_list
        ]
        if vector_keys:
            load_vectors(*vector_keys, group_name="added_vector")

    def _add_raster(self):
        # flatten list of list
        raster_keys = [key for cb, key in self.RASTER_CHECKBOX_KEY_MAP.items() if cb.isChecked()]
        if raster_keys:
            load_rasters(*raster_keys, group_name="added_raster")

    def _add_wms(self):
        # flatten list of list
        wms_keys = [key for cb, key in self.WMS_CHECKBOX_KEY_MAP.items() if cb.isChecked()]
        if wms_keys:
            load_wms(*wms_keys, group_name="added_wms")
