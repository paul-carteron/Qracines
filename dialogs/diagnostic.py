from PyQt5.QtWidgets import *
from .diagnostic_dialog import Ui_DiagnosticDialog
from qgis.core import *

# import manager
from ..core.db.manager import DatabaseManager
from ..core.layer.manager import LayerManager

# Import from utils folder
from ..utils.variable_utils import *
from ..utils.layer_utils import *
from ..utils.qfield_utils import *
from ..utils.path_manager import *

import os

class DiagnosticDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_DiagnosticDialog()
        self.ui.setupUi(self)
        self.project = QgsProject.instance()

        self.essences_layer = DatabaseManager().load_essences("Ess")
    
    @staticmethod
    def placette_layer():
        placette_fields = [
            ("PLACETTE", QVariant.String), ("PLTM_PARC", QVariant.String), ("PLTM_TYPE", QVariant.String), ("PLTM_RICH", QVariant.String),
            ("PLTM_STADE", QVariant.String), ("PLTM_PB", QVariant.String), ("PLTM_SANT", QVariant.String), ("PLTM_MEC", QVariant.String),
            ("PLTM_HISTO", QVariant.String), ("PLTM_AME", QVariant.String), ("PLTM_RMQ", QVariant.String), ("PICTURES", QVariant.String),
            ("TSE_DENS", QVariant.String), ("TSE_VOL", QVariant.Double), ("TSE_NATURE", QVariant.String), ("TSE_POTEN", QVariant.String),
            ("TSE_CLOISO", QVariant.String), ("TSE_RMQ", QVariant.String),
            # Valeur d'avenir
            ("VA_REG", QVariant.String), ("VA_TX_TROUEE", QVariant.Double), ("VA_NHA", QVariant.Double), ("VA_VEG_CO", QVariant.String),
            ("VA_TX_DEG", QVariant.Double), ("VA_DEG", QVariant.String), ("VA_RMQ", QVariant.String),
        ]
        placette_layer = create_memory_layer('Placette', placette_fields, 'Point')
        return placette_layer
    
    @staticmethod
    def transect_layer():
        transect_fields = [
            ("UUID", QVariant.String), ("PLTM_PARC", QVariant.String), ("PLTM_GROUPE", QVariant.String), ("TR_TYPE_ESS", QVariant.String),
            ("TR_ESS", QVariant.String), ("TR_DIAM", QVariant.Int), ("TR_EFFECTIF", QVariant.Int), ("TR_HAUTEUR", QVariant.Int)
        ]
        transect_layer = create_memory_layer('Transect', transect_fields, 'Point')
        return transect_layer

    @staticmethod
    def limite_layer():
        limite_fields = [("TYPE", QVariant.String), ("RMQ", QVariant.String)]
        limite_layer = create_memory_layer('Limite', limite_fields, 'LineString')
        return limite_layer

    @staticmethod
    def picto_layer():
        picto_fields = [("TYPE", QVariant.String), ("NATURE", QVariant.String), ("PICTURES", QVariant.String)]
        picto_layer = create_memory_layer('Picto', picto_fields, 'Point')
        return picto_layer
    
    @staticmethod
    def gha_layer():
        gha_fields = [("RES_ESS", QVariant.String), ("RES_G", QVariant.Int), ("PLACETTE", QVariant.String)]
        gha_layer = create_memory_layer('Gha', gha_fields)
        return gha_layer
    
    @staticmethod
    def tse_layer():
        tse_fields = [("TSE_ESS", QVariant.String), ("TSE_DM", QVariant.String), ("PLACETTE", QVariant.String)]
        tse_layer = create_memory_layer('Tse', tse_fields)
        return tse_layer
    
    @staticmethod
    def reg_layer():
        reg_fields = [("REG_ESS", QVariant.String), ("REG_STADE", QVariant.String), ("REG_ETAT", QVariant.String), ("PLACETTE", QVariant.String)]
        reg_layer = create_memory_layer('Reg', reg_fields)
        return reg_layer
    
    @staticmethod
    def va_ess_layer():
        va_ess_fields = [
            ("PLACETTE", QVariant.String), ("VA_ESS", QVariant.String), ("VA_STADE", QVariant.String),
            ("VA_AGE_APP", QVariant.Int), ("VA_HT", QVariant.Double), ("VA_ELAG", QVariant.String),
            ("VA_TX_HA", QVariant.Double), ("CUMUL_TX_VA", QVariant.Double)
        ]
        va_ess_layer = create_memory_layer('Va_ess', va_ess_fields)
        return va_ess_layer

    def load_parcellaire(self):
        """
        Try to load a Parcellaire layer from disk, collect its unique
        PARCELLE values, and set self.has_parcellaire / self.parcelles_str.
        Returns the QgsVectorLayer if successful, or None otherwise.
        """
        parc_path = get_path("parcellaire")
        if not os.path.exists(parc_path):
            self.parcelles_str = None
            return None

        layer = QgsVectorLayer(parc_path, 'Parcellaire', 'ogr')
        if not layer.isValid():
            self.parcelles_str = None
            return None

        # collect unique parcel identifiers
        self.parcelles_str = {feat["PARCELLE"] for feat in layer.getFeatures()}
        return layer

    def create_and_load_gpkg(self):

        layers = [
                self.placette_layer, 
                self.transect_layer,
                self.limite_layer,
                self.picto_layer,
                self.gha_layer,
                self.tse_layer,
                self.reg_layer,
                self.va_ess_layer,
                self.essences_layer
        ]

        #load & append parcellaire if available
        parc_layer = self.load_parcellaire()
        if parc_layer:
            layers.append(parc_layer)

        # Create gpkg
        params = {
            'LAYERS': layers,
            'OUTPUT': get_path("diagnostic"),
            'OVERWRITE': True,}
        processing.run("native:package", params)

        # load layers from gpkg
        add_layers_from_gpkg(get_path("diagnostic"))

        return None
    
    def apply_style(self):
        # (layer_name, key for config)
        layer_style = [
            ('Placette','placette'),
            ('Transect', 'transect'),
            ('Picto', 'picto'),
            ('Limite', 'limite'),
            ('Gha', 'gha'),
            ('Tse', 'tse'),
            ('Reg', 'reg'),
            ('Va_ess', 'va_ess'),
            ('Ess', 'ess'),
            ] 
        
        for (layer_name, key) in layer_style:
            layer = self.project.mapLayersByName(layer_name)[0]
            style_path = get_style(key)
            if layer.loadNamedStyle(style_path):
                    layer.triggerRepaint()

    def configure_placette(self, layer_manager):
        layer_manager.set_constraint('PLACETTE', QgsFieldConstraints.ConstraintUnique)

        if self.parcelles_str:
            layer_manager.fields.add_value_map('PLTM_PARC', {'map': self.parcelles_str})

    def configure_transect(self, layer_manager):
        if self.parcelles_str:
            layer_manager.fields.add_value_map('PLTM_PARC', {'map': self.parcelles_str})


    def configure_va_ess_layer(manager):
            # Set constraints and default values
            layer_manager.set_constraint("VA_TX_HA", QgsFieldConstraints.ConstraintNotNull, QgsFieldConstraints.ConstraintStrengthSoft)
            expression = '"CUMUL_TX_VA" + "VA_TX_HA" = 100'
            description = "La somme de VA_TX_HA et de CUMUL_TX_VA doit être égale à 100."
            layer_manager.set_constraint_expression("VA_TX_HA", expression, description, strength=QgsFieldConstraints.ConstraintStrengthSoft)
            
            default_value = ("""aggregate(layer:='Va_ess', aggregate:='sum', expression:="VA_TX_HA", filter:="PLACETTE" = attribute(@parent, 'PLACETTE'))""")
            layer_manager.set_default_value("CUMUL_TX_VA", default_value)
            layer_manager.set_read_only('CUMUL_TX_VA')

            layer_manager.set_constraint("VA_ESS", QgsFieldConstraints.ConstraintNotNull, QgsFieldConstraints.ConstraintStrengthHard)
            layer_manager.set_constraint("VA_AGE_APP", QgsFieldConstraints.ConstraintNotNull, QgsFieldConstraints.ConstraintStrengthHard)
            layer_manager.set_constraint("VA_TX_HA", QgsFieldConstraints.ConstraintNotNull, QgsFieldConstraints.ConstraintStrengthHard)
            
            display_expression = """concat(coalesce("VA_ESS", 'NULL'), ' - ', "VA_TX_HA", '%')"""
            layer_manager.set_display_expression(display_expression)

            # Configure form
            fields_name = ["VA_ESS", "VA_STADE", "VA_AGE_APP", "VA_HT", "VA_ELAG", "VA_TX_HA", "CUMUL_TX_VA"]
            layer_manager.init_drag_and_drop_form()
            layer_manager.add_fields_to_form(fields_name)
            
            # Add value map
            essence_map = DatabaseManager().fetch_essence_map()
            layer_manager.add_value_map("VA_ESS", essence_map)


    def create_diagnostic(self):

        self.create_and_load_gpkg()

        placette = LayerManager("Placette")
        transect = LayerManager("Transect")
        va_ess = LayerManager('Va_ess')

        for layer_pair in [('Placette', 'Gha'), ('Placette', 'Tse'), ('Placette', 'Reg'), ('Placette', 'Va_ess')]:
            create_relation(*layer_pair, 'PLACETTE', 'PLACETTE', f'{layer_pair[0]}_{layer_pair[1]}', layer_pair[1])

        self.apply_style()

        self.configure_placette()
        self.configure_transect()
