from pathlib import Path
import processing

from qgis.PyQt.QtWidgets import QDialog
from .pedology_dialog import Ui_PedologyDialog
from qgis.core import (
  QgsProcessing,
  QgsProject
)
from PyQt5.QtWidgets import QMessageBox

from qgis.utils import iface

from ..utils.path_manager import get_guides, get_style, get_stations, get_path
from ..utils.variable_utils import clear_project, get_project_variable
from ..utils.layer_utils import load_vectors, load_rasters, replier, create_map_theme, zoom_on_layer, add_layers_from_gpkg, create_relation, set_layers_readonly
from ..utils.qfield_utils import package_for_qfield
from ..core.layer_factory import LayerFactory
from ..core.layer import LayerManager

class PedologyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.project = QgsProject.instance()
        self.ui = Ui_PedologyDialog()
        self.ui.setupUi(self)
        
        # --- initialise forest name ---
        self.ui.le_forest_name.setText(get_project_variable("forest_prefix") or "Pas de forêt sélectionnée")

        # --- Connect checkbox package_for_qfield ---
        self.ui.cb_package_for_qfield.toggled.connect(self.toggle_fw_editability)

        # --- Populate cob_stations with guides ---
        guides = get_guides()
        self.ui.cob_stations.addItems(guides)
        
        # --- Connect OK and REJECT button ---
        self.ui.buttonBox.accepted.connect(self.create_pedology)
        self.ui.buttonBox.rejected.connect(self.reject)
    
    # Override exec_() so i can check that a forest is selected before loading the dialog (see self.pedology_dialog.exec_() in Qsequoia2.py)
    def exec_(self):
        pedology_path = get_path("pedology_qfield")
        if not pedology_path:
            return QDialog.Rejected

        default_dir = pedology_path.parent
        default_dir.mkdir(parents=True, exist_ok=True)
        self.ui.fw_package_outdir.setFilePath(str(default_dir))
        self.ui.fw_package_outdir.setStorageMode(self.ui.fw_package_outdir.GetDirectory)

        return super().exec_()

    def toggle_fw_editability(self, checked):
        self.ui.fw_package_outdir.setEnabled(checked)
        self.ui.le_package_title.setEnabled(checked)

    def create_pedology(self):

        clear_project()
        
        guide = self.ui.cob_stations.currentText()
        stations = get_stations(guide)
        
        # Vector import
        load_vectors('prop_line', 'prop_diag_line', 'pf_line', 'pf_diag_line', 'pf_polygon', 'sspf_polygon', 'sspf_diag_polygon', 'ua_polygon')
        zoom_on_layer('prop_line')

        # Raster import
        load_rasters('plt','plt_anc','irc','rgb','mnh','scan25', group_name="RASTER")

        replier()
        
        layers = [LayerFactory.create("sondage", "PEDOLOGIE"), LayerFactory.create("horizons", "PEDOLOGIE")]

        result = processing.run("native:package", {
            'LAYERS':      layers,
            'OUTPUT':      QgsProcessing.TEMPORARY_OUTPUT,
            'OVERWRITE':   True,
            'SAVE_STYLES': False
        })

        self.gpkg_path = result['OUTPUT']
        add_layers_from_gpkg(self.gpkg_path)

        # Création de la relation
        create_relation('sondage', 'horizons', 'uuid', 'sondage', 'sondage_horizons','sondage')
        
        # Application du style aux couches créées
        for key in ("sondage", "horizons"):
            layers = self.project.mapLayersByName(key)
            if not layers:
                continue
            layer = layers[0]
            style_path = get_style(key)
            if layer.loadNamedStyle(str(style_path)):
                layer.triggerRepaint()

        sondage_mgr = LayerManager('sondage')
        sondage_mgr.fields.add_value_map('station', {'map': [{str(s): str(s)} for s in stations]})
        
        # Création des thèmes
        map_themes = [
                ("1_PLT",
                 ['plt', 'prop_line', 'pf_line', 'pf_polygon', 'sspf_polygon', 'ua_polygon'],
                 ['plt_anc', 'irc', 'rgb', 'mnh', 'scan25', 'prop_diag_line', 'pf_diag_line', 'sspf_diag_polygon']),
                ("2_PLT-ANC",
                 ['plt_anc', 'prop_line', 'pf_line', 'pf_polygon'], 
                 ['plt', 'irc', 'rgb', 'mnh', 'scan25', 'prop_diag_line', 'pf_diag_line', 'sspf_polygon', 'sspf_diag_polygon', 'ua_polygon']),
                ("3_IRC",
                 ['irc', 'prop_diag_line', 'pf_diag_line', 'pf_polygon', 'sspf_diag_polygon', 'ua_polygon'],
                 ['plt', 'plt_anc', 'rgb', 'mnh', 'scan25', 'prop_line', 'pf_line', 'sspf_polygon']),
                ("4_RGB",
                 ['rgb', 'prop_diag_line', 'pf_diag_line', 'pf_polygon', 'sspf_diag_polygon', 'ua_polygon'],
                 ['plt', 'plt_anc', 'irc', 'mnh', 'scan25', 'prop_line', 'pf_line', 'sspf_polygon']),
                ("5_MNH",
                 ['mnh', 'prop_line', 'pf_line', 'pf_polygon', 'sspf_polygon', 'ua_polygon'],
                 ['plt', 'plt_anc', 'irc', 'rgb', 'scan25', 'prop_diag_line', 'pf_diag_line', 'sspf_diag_polygon']),
                ("6_SCAN25",
                 ['scan25', 'prop_line', 'pf_line', 'pf_polygon', 'sspf_polygon', 'ua_polygon'],
                 ['plt', 'plt_anc', 'irc', 'rgb', 'mnh', 'prop_diag_line', 'pf_diag_line', 'sspf_diag_polygon'])
                ]
        for theme in map_themes:
            create_map_theme(*theme)
            
        # Verrouillage des couches
        layer_names = ['prop_line', 'prop_diag_line', 'pf_line', 'pf_diag_line', 'pf_polygon', 'sspf_polygon', 'sspf_diag_polygon', 'ua_polygon']
        set_layers_readonly(*layer_names)
    
        if self.ui.cb_package_for_qfield.isChecked():
            self._package_for_qfield()

    def _package_for_qfield(self):
        forest_prefix = get_project_variable("forest_prefix")

        outdir = Path(self.ui.fw_package_outdir.filePath())
        if not outdir.exists():
            QMessageBox.warning(self, "Invalid folder", "Please choose a valid directory.")
            return
        
        custom_title = self.ui.le_package_title.text()
        filename = custom_title if custom_title else f"{forest_prefix}_pedology"
        
        package_for_qfield(iface, self.project, outdir, filename)
