from .pedology_dialog import Ui_PedologyDialog
from qgis.core import QgsProcessing, QgsProject, Qgis
from qgis.utils import iface

from ..utils.path_manager import get_guides, get_style, get_stations, get_path
from ..utils.variable_utils import clear_project, get_project_variable
from ..utils.layer_utils import load_vectors, load_rasters, replier, create_map_theme
from ..utils.qfield_utils import add_layers_from_gpkg, create_relation, set_layers_readonly, create_qfield_package

from ..core.layer_factory import LayerFactory
from ..core.layer import LayerManager

import processing

class PedologyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.ui = Ui_PedologyDialog()
        self.ui.setupUi(self)
        
        # Liste des guides possibles
        guides = get_guides()
        self.ui.comboBox.addItems(guides)
        
        self.ui.buttonBox.clicked.connect(self.create_pedology)
        
    def create_pedology(self):

        clear_project()
        
        guide = self.ui.comboBox.currentText()
        stations = get_stations(guide)
        
        # Vector import
        load_vectors('prop_line', 'prop_diag_line', 'pf_line', 'pf_diag_line', 'pf_polygon', 'sspf_polygon', 'sspf_diag_polygon', 'ua_polygon')
    
        # Raster import
        load_rasters('plt','plt_anc','irc','rgb','mnh','scan25')
        replier()
        
        layers = [
            LayerFactory.create("sondage"),
            LayerFactory.create("horizons"),
            self.essences_layer
        ]

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
        
        # Actulisation du style
        for key in ("sondage", "horizons"):
            layers = self.project.mapLayersByName(key)
            if not layers:
                continue
            layer = layers[0]
            style_path = get_style(key)
            if layer.loadNamedStyle(style_path):
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
        set_layers_readonly(layer_names)
        
        # Enregistrement du projet
        project = QgsProject.instance()
        save_path = get_path("pedology")
        project.write(save_path)
        
        self.iface.messageBar().pushMessage("QSequoia2", "PEDOLOGY généré avec succès", level=Qgis.Success, duration=10)
        
        # Création du paquet
        forest_directory = get_project_variable("forest_directory")
        create_qfield_package(forest_directory, save_path)
        project.write()
