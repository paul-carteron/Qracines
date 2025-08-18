from PyQt5.QtWidgets import QDialog
from .add_data_dialog import Ui_AddDataDialog
from itertools import chain

# Import from utils folder
from ...utils.variable import get_global_variable, get_project_variable, get_project_variable
from ...utils.layers import *

class AddDataDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.ui = Ui_AddDataDialog()
        self.ui.setupUi(self)
        
        self.VECTOR_CHECKBOX_KEY_MAP = {
            self.ui.cb_vector_route: ['route_polygon', 'route_line'],
            self.ui.cb_vector_pf: ['pf_polygon', 'pf_line'],
            self.ui.cb_vector_sspf: ['sspf_polygon', 'sspf_line'],
            self.ui.cb_vector_ua: ['ua_polygon_ame', 'ua_polygon_occup', 'ua_polygon_plt', 'ua_polygon'],
            self.ui.cb_vector_topo: ['topo_line'],
        }

        self.RASTER_CHECKBOX_KEY_MAP = {
            self.ui.cb_raster_plt: "plt",
            self.ui.cb_raster_plt_anc: "plt_anc",
            self.ui.cb_raster_irc: "irc",
            self.ui.cb_raster_rgb: "rgb",
            self.ui.cb_raster_mnh: "mnh",
            self.ui.cb_raster_mnt: "mnt",
            self.ui.cb_raster_scan25: "scan25",
        }

        self.WMS_CHECKBOX_KEY_MAP = {
            # SCAN
            self.ui.cb_wms_scan100: "wms_scan1000",
            self.ui.cb_wms_scan1000: "wms_scan100",
            self.ui.cb_wms_scan25: "wms_scan25",
            self.ui.cb_wms_scan25_grey: "wms_scan25_grey",
            # ORTHO
            self.ui.cb_wms_irc: "wms_irc",
            self.ui.cb_wms_rgb: "wms_rgb",
            self.ui.cb_wms_spot_2023: "wms_spot_2023",
            # ORTHOHISTO
            self.ui.cb_wms_histo_1950: "wms_histo_1950",
            self.ui.cb_wms_histo_1965: "wms_histo_1965",
            self.ui.cb_wms_histo_1980: "wms_histo_1980",
            self.ui.cb_wms_histo_2000: "wms_histo_2000", 
            self.ui.cb_wms_histo_2006: "wms_histo_2006",
            self.ui.cb_wms_histo_2011: "wms_histo_2011",
            # AUTRES
            self.ui.cb_wms_geol: "wms_geol",
            self.ui.cb_wms_pci: "wms_pci",
        }
        
        self.TERRAIN_CHECKBOX_KEY_MAP = {
            self.ui.cb_terrain_expertise: "expertise",
            self.ui.cb_terrain_inventaire: "inventaire",
        }

        self._all_checkbox_maps = (
            self.VECTOR_CHECKBOX_KEY_MAP,
            self.RASTER_CHECKBOX_KEY_MAP,
            self.WMS_CHECKBOX_KEY_MAP,
            self.TERRAIN_CHECKBOX_KEY_MAP,
        )
    
    def _reset_checkboxes(self):
        """Uncheck every checkbox in all our maps."""
        for chk in chain.from_iterable(m.keys() for m in self._all_checkbox_maps):
            chk.setChecked(False)

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
            load_vectors(*vector_keys, group_name="VECTOR")

    def _add_raster(self):
        # flatten list of list
        raster_keys = [key for cb, key in self.RASTER_CHECKBOX_KEY_MAP.items() if cb.isChecked()]
        if raster_keys:
            load_rasters(*raster_keys, group_name="RASTER")

    def _add_wms(self):
        # flatten list of list
        wms_keys = [key for cb, key in self.WMS_CHECKBOX_KEY_MAP.items() if cb.isChecked()]
        if wms_keys:
            load_wms(*wms_keys, group_name="WMS")

    def _add_terrain(self):
        # flatten list of list
        gpkg_keys = [key for cb, key in self.TERRAIN_CHECKBOX_KEY_MAP.items() if cb.isChecked()]
        if gpkg_keys:
            [load_gpkg(get_path(key), group_name="TERRAIN") for key in gpkg_keys]

    def accept(self):
        self._check_variables()

        self._add_vector()
        self._add_raster()
        self._add_wms()
        self._add_terrain()
        
        self._reset_checkboxes()

        super().accept()