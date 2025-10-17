from pathlib import Path
import processing

from qgis.core import (
    QgsProject,
    QgsProcessing,
    QgsFieldConstraints,
    QgsFeatureRequest,
    QgsExpression,
    QgsRendererCategory,
    QgsCategorizedSymbolRenderer,
    QgsSymbol
)

from qgis.utils import iface

from PyQt5.QtCore import QVariant
from PyQt5.QtGui import QColor

from ...core.layer_factory import LayerFactory
from ...core.layer.manager import LayerManager
from ...utils.config import get_peuplements, get_limites
from ...utils.layers import load_gpkg, create_relation, load_vectors

class DiagnosticService:

    def __init__(self, essences_layer: dict):
        self.iface = iface
        self.project = QgsProject.instance()
        self.root = self.project.layerTreeRoot()
        self.essences_layer = essences_layer

    def run(self):
        """
        Runs the full workflow. 
        Returns the output_dir path (as str) if packaging was done, otherwise None.
        Raises on any error.
        """
        
        print("_create_and_load_gpkg")
        self._create_and_load_gpkg()

        print("_create_relations")
        self._create_relations()

        # PLACETTE
        print("configure PLACETTE layer")
        placette_manager = LayerManager("Placette")
        self._init_placette_form(placette_manager)
        self._configure_placette(placette_manager)
        placette_manager.layer.setCustomProperty("QFieldSync/value_map_button_interface_threshold", 10)
        
        # TRANSECT
        print("configure TRANSECT layer")
        transect_manager = LayerManager("Transect")
        self._init_transect_form(transect_manager)
        self._configure_transect(transect_manager)
        transect_manager.layer.setCustomProperty("QFieldSync/value_map_button_interface_threshold", 99)

        # GHA
        print("configure GHA layer")
        gha_manager = LayerManager("Gha")
        self._init_gha_form(gha_manager)  
        self._configure_gha(gha_manager)  
        gha_manager.layer.setCustomProperty("QFieldSync/value_map_button_interface_threshold", 99)

        # VA
        va_manager = LayerManager("Va")
        self._init_va_form(va_manager)  
        self._configure_va(va_manager)  
        va_manager.layer.setCustomProperty("QFieldSync/value_map_button_interface_threshold", 99)

        return self.gpkg_path

    def _create_and_load_gpkg(self):

        layers = [
            LayerFactory.create("Placette", "DIAGNOSTIC"),
            LayerFactory.create("Transect", "DIAGNOSTIC"),
            LayerFactory.create("Limite", "DIAGNOSTIC"),
            LayerFactory.create("Gha", "DIAGNOSTIC"),
            LayerFactory.create("Tse", "DIAGNOSTIC"),
            LayerFactory.create("Va", "DIAGNOSTIC"),
            self.essences_layer,
        ]

        result = processing.run("native:package", {
            'LAYERS':      layers,
            'OUTPUT':      QgsProcessing.TEMPORARY_OUTPUT,
            'OVERWRITE':   True,
            'SAVE_STYLES': False
        })

        self.gpkg_path = result['OUTPUT']
        load_gpkg(self.gpkg_path, group_name="DIAGNOSTIC")

    def _create_relations(self):
        pairs = [
            ('Placette', 'Gha'),
            ('Placette', 'Tse'),
            ('Placette', 'Va')
        ]
        for parent, child in pairs:
            create_relation(
                parent_name = parent, child_name = child,
                parent_field = 'UUID', child_field = 'UUID',
                relation_id = f'{parent}_{child}',
                relation_name = child
            )
    
    @staticmethod
    def _init_placette_form(placette_manager):

        placette_fb = placette_manager.forms
        placette_fb.init_drag_and_drop_form()

        # ve: stand for visibility_expression
        forest_plt = "('FRF', 'FIF', 'REF', 'PLF', 'FRM', 'FIM', 'REM', 'PLM', 'FRR', 'FIR', 'RER', 'PLR', 'PEU', 'MFT', 'MRT', 'MMT', 'TSB', 'TSN')"
        va_plt = "('REF', 'PLF', 'REM', 'PLM', 'RER', 'PLR')"

        forest_ve = f"\"PLT_TYPE\" IN {forest_plt}"
        va_ve = f"\"PLT_TYPE\" IN {va_plt}"

        placette_fb.add_fields(
            "COMPTEUR", "PLT_PARCELLE", "PLT_TYPE", "PLT_AME", "PLT_RMQ", "PLT_PHOTO",
            name="Général", type = "tab")

        placette_fb.add_fields(
            "PLT_RICH", "PLT_STADE", "PLT_DMOY", "PLT_ELAG", "PLT_SANIT", "PLT_CLOISO", "PLT_MECA",
            name = "Peuplement", visibility_expression = forest_ve, type = "tab"
        )


        placette_fb.add_relation("Gha", name="Gha", visibility_expression = forest_ve, type="tab")
        placette_fb.add_relation("Tse", name="Taillis", visibility_expression = forest_ve, type="tab")
        placette_fb.add_relation("Va", name="Plant/Régé", visibility_expression = va_ve, type="tab")
        placette_fb.add_fields("VA_HT", "VA_TX_TROUEE", "VA_VEG_CON", "VA_TX_DEG", "VA_PROTECT", name="Plant/Régé", visibility_expression = va_ve, type="tab")

    @staticmethod
    def _configure_placette(placette_manager):
        placette_f = placette_manager.fields

        # ALIASES
        aliases = [
            ("COMPTEUR", "Placette n°"),
            ("PLT_PARCELLE", "PRF/SPRF"),
            ("PLT_TYPE", "Type de peuplement"),
            ("PLT_RICH", "Richesse"),
            ("PLT_STADE", "Stade"),
            ("PLT_DMOY", "Diamètre Moyen (cm)"),
            ("PLT_ELAG", "Élagage"), 
            ("PLT_SANIT", "Sanitaire"), 
            ("PLT_CLOISO", "Cloisonnement"), 
            ("PLT_MECA", "Mécanisation"),
            ("PLT_AME", "Aménagement"), 
            ("PLT_RMQ", "Remarque"), 
            ("PLT_PHOTO", "Photo"),]
        
        for field, alias in aliases:
            placette_f.set_alias(field, alias)

        # UUID
        # If apply_on_update=True, uuid() resets on each children edit: 
        # - Create parent → UUID=A 
        # - Add first child → FK=A 
        # - Edit another child → UUID becomes B (child’s FK=A breaks under Composition) 
        # - Add second child → FK=B 
        # Only the last child stays linked. Using apply_on_update=False keeps the UUID stable so all children link correctly.
        field_name = "UUID"
        placette_f.set_constraint(field_name, QgsFieldConstraints.ConstraintUnique)
        placette_f.set_default_value(field_name, "uuid()", apply_on_update=False)
        placette_f.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)

        # COMPTEUR
        field_name = "COMPTEUR"
        placette_f.set_read_only(field_name)
        placette_f.set_default_value(field_name, 'count("fid") + 1')

        # PLT_TYPE
        field_name = "PLT_TYPE"
        peuplements = get_peuplements()
        placette_f.add_value_map(field_name, {'map': [{str(name): str(code)} for code, name in peuplements.items()]})
        placette_f.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)

        # PLT_RICH
        richesse = {
            'TRI': 'Très riche',
            'RRI': 'Riche',
            'MRI': 'Moy. riche',
            'PPA': 'Pauvre',
            'TPA': 'Ruiné',
            'SIN': 'Sinistré'
        }
        placette_f.add_value_map('PLT_RICH', {'map': [{str(name): str(code)} for code, name in richesse.items()]})

        # PLT_STADE
        stade = {
            'SFO': 'Semis / Fourré',
            'GPE': 'Gaulis / Perchis',
            'JEU': 'Jeune',
            'ADU': 'Adulte',
            'MAT': 'Mature',
            'EXP': 'Exploitable',
            'NEX': 'Non exploitable'
        }
        placette_f.add_value_map('PLT_STADE', {'map': [{str(name): str(code)} for code, name in stade.items()]})

        # PLT_DMOY
        placette_f.add_range('PLT_DMOY', {'AllowNull': True, 'Max': 200, 'Min': 0, 'Precision': 0, 'Step': 5})

        # PLT_ELAG
        elagage = {'2m':'2m', '4m': '4m', '6m': '6m'}
        placette_f.add_value_map('PLT_ELAG', {'map': [{str(name): str(code)} for code, name in elagage.items()]})

        # PLT_SANIT
        sanitaire = {
            'AFF_EPARS': 'Affaiblissements épars',
            'AFF_GEN': 'Affaiblissements généralisés',
            'DEP_EPARS': 'Dépérissements épars',
            'DEP_GEN': 'Dépérissements généralisés'
        }
        placette_f.add_value_map('PLT_SANIT', {'map': [{str(name): str(code)} for code, name in sanitaire.items()]})

        # PLT_CLOISO
        cloiso = {
            'Irrégulier': 'Irrégulier',
            '7m': '7m',
            '12m': '12m',
            '15m': '15m',
            '20m': '20m',
            '25m': '25m',
            '30m': '30m',
        }
        placette_f.add_value_map('PLT_CLOISO', {'map': [{str(name): str(code)} for code, name in cloiso.items()]})

        # PLT_MECA
        mecanisable = {
            'M': 'Mécanisable',
            'M_SEMI': 'Semi-mécanisable',
            'M_PARTIE': 'Mécanisable en partie',
            'M_TREUIL': 'Mécanisable - Treuil',
            'NM_PENTE': 'Non mécanisable - Pente',
            'NM_ROCHE': 'Non mécanisable - Roches',
            'NM_HUMIDE': 'Non mécanisable - Humide'
        }
        placette_f.add_value_map('PLT_MECA', {'map': [{str(name): str(code)} for code, name in mecanisable.items()]})

        # VA_HT
        placette_f.add_range("VA_HT", {'AllowNull': False, 'Max': 50, 'Min': 0, 'Precision': 0, 'Step': 1})

        # VA_TX_TROUEE
        tx_trouee = {         
            '<10': '<10% (1/10)',
            '10': '10% (1/10)',
            '20': '20% (1/5)',
            '25': '25% (1/4)',
            '33': '33% (1/3)',
            '50': '50% (1/2)',
            '66': '66% (2/3)',
            '>66': '+ de 66% (2/3)',
        }
        placette_f.add_value_map('VA_TX_TROUEE', {'map': [{str(name): str(code)} for code, name in tx_trouee.items()]})

        # VA_VEG_CON
        veg_con = {
            '2': 'Dense / Nettoyage urgent',
            '1': 'Moyenne / Nettoyage à programmer',
            '0': 'Maitrisée / Pas de nettoyage',
        }
        placette_f.add_value_map('VA_VEG_CON', {'map': [{str(name): str(code)} for code, name in veg_con.items()]})

        # VA_TX_DEG
        tx_deg = {         
            '<10': '<10% (1/10)',
            '10': '10% (1/10)',
            '20': '20% (1/5)',
            '25': '25% (1/4)',
            '33': '33% (1/3)',
            '50': '50% (1/2)',
            '66': '66% (2/3)',
            '>66': '+ de 66% (2/3)',
        }
        placette_f.add_value_map('VA_TX_DEG', {'map': [{str(name): str(code)} for code, name in tx_deg.items()]})

        # VA_PROTECT
        protect = {
            'CLOTURE': 'Clôture',
            'INDIV_MECA': 'Individuelle méca',
            'INDIV_CHIMIQUE': 'Individuelle chimique',
        }
        placette_f.add_value_map('VA_PROTECT', {'map': [{str(name): str(code)} for code, name in protect.items()]})

        return None

    @staticmethod
    def _init_transect_form(transect_manager):

        transect_fb = transect_manager.forms
        transect_fb.init_drag_and_drop_form()

        transect_fb.add_fields("TR_PARCELLE")
        transect_fb.add_fields("TR_TYPE_ESS", "TR_ESS", name = "Essence", columns=2)
        transect_fb.add_fields("TR_DIAM", "TR_HAUTEUR", name = "Dendrométrie", columns=2)
        transect_fb.add_fields("TR_EFFECTIF")
    
    def _configure_transect(self, transect_manager):
        transect_f = transect_manager.fields

        # ALIASES
        aliases = [
            ("TR_PARCELLE", "PRF/SPRF"),
            ("TR_TYPE_ESS", "Type Essence"),
            ("TR_ESS", "Essence"),
            ("TR_DIAM", "Diamètre (cm)"),
            ("TR_HAUTEUR", "Hauteur (m)"),
            ("TR_EFFECTIF", "Effectif"),]
        
        for field, alias in aliases:
            transect_f.set_alias(field, alias)

        # UUID
        # If apply_on_update=True, uuid() resets on each children edit: 
        # - Create parent → UUID=A 
        # - Add first child → FK=A 
        # - Edit another child → UUID becomes B (child’s FK=A breaks under Composition) 
        # - Add second child → FK=B 
        # Only the last child stays linked. Using apply_on_update=False keeps the UUID stable so all children link correctly.
        field_name = "UUID"
        transect_f.set_constraint(field_name, QgsFieldConstraints.ConstraintUnique)
        transect_f.set_default_value(field_name, "uuid()", apply_on_update=False)
        transect_f.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)

        # TR_TYPE_ESS
        field_name = "TR_TYPE_ESS"
        types = {f["type"]: f["type"] for f in self.essences_layer.getFeatures()}
        transect_f.add_value_map(field_name, {'map': [{str(name): str(code)} for code, name in types.items()]})

        # TR_ESS
        field_name = "TR_ESS"
        transect_f.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        config = {
            'FilterExpression': f"\"type\" = current_value('TR_TYPE_ESS')",
            'Key': 'fid',
            'LayerName': self.essences_layer.name(),
            'Value': 'essence_variation'
        }
        transect_f.add_value_relation(field_name, config)
        transect_f.set_default_value(field_name, "current_value('TR_TYPE_ESS')")

        # TR_DIAM
        field_name = "TR_DIAM"
        transect_f.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        transect_f.add_value_map(field_name, {'map': [{str(d): str(d)} for d in range(15, 110 + 1, 5)]})
        expression = '"TR_DIAM" != \'\''
        description = "Le champ TR_DIAM ne peut pas être vide."
        transect_f.set_constraint_expression(field_name, expression, description, QgsFieldConstraints.ConstraintStrengthHard)

        # TR_HAUTEUR
        field_name = "TR_HAUTEUR"
        transect_f.add_value_map(field_name, {'map': [{str(h): str(h)} for h in range(3, 30 + 1)]})

        # TR_EFFECTIF
        field_name = "TR_EFFECTIF"
        transect_f.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        transect_f.add_range(field_name, {'AllowNull': False, 'Max': 1000, 'Min': 0, 'Precision': 0, 'Step': 1})
        transect_f.set_default_value(field_name, '1', False)

    @staticmethod
    def _init_gha_form(gha_manager):
        gha_manager.forms.init_drag_and_drop_form()
        gha_manager.forms.add_fields("GHA_ESS", "GHA_G")

    def _configure_gha(self, gha_manager):
        gha_f = gha_manager.fields

        # ALIASES
        aliases = [
            ("GHA_ESS", "Essence"),
            ("GHA_G", "Surface terrière")
        ]
        
        for field, alias in aliases:
            gha_f.set_alias(field, alias)
        
        # DISPLAY EXPRESSION
        display_expression = """
            WITH_VARIABLE(
                'ess',
                get_feature('Essences', 'fid', "GHA_ESS"),
                concat(
                    attribute(@ess, 'essence_variation'),
                    ' : ',
                    "GHA_G",
                    ' m²/ha '
                )
            )
            """
        gha_manager.set_display_expression(display_expression)

        # GHA_ESS
        field_name = "GHA_ESS"
        gha_f.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        config = {
            'FilterExpression': '"variation" IS NULL',
            'Key': 'fid',
            'LayerName': self.essences_layer.name(),
            'Value': 'essence_variation'
        }
        gha_f.add_value_relation(field_name, config)

        # GHA_G
        field_name = "GHA_G"
        gha_f.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        gha_f.set_constraint_expression(field_name, f'"{field_name}" > 0', "La surface terrière doit être supérieur à 0", strength=QgsFieldConstraints.ConstraintStrengthHard)
        gha_f.add_range(field_name, {'AllowNull': False, 'Max': 100, 'Min': 0, 'Precision': 0, 'Step': 1})

    @staticmethod
    def _init_va_form(va_manager):
        va_manager.forms.init_drag_and_drop_form()
        va_manager.forms.add_fields("VA_ESS", "VA_TX_HA", "VA_CUMUL_TX_VA")

    def _configure_va(self, va_manager):
        va_f = va_manager.fields

        # ALIASES
        aliases = [
            ("VA_ESS", "Essence"),
            ("VA_TX_HA", "Taux de recouvrement"),
            ("VA_CUMUL_TX_VA", "Cumul des recouvrements"),
        ]
        
        for field, alias in aliases:
            va_f.set_alias(field, alias)
        
        # DISPLAY EXPRESSION
        display_expression = """
            WITH_VARIABLE(
                'ess',
                get_feature('Essences', 'fid', "VA_ESS"),
                concat(
                    attribute(@ess, 'essence_variation'),
                    ' : ',
                    "VA_TX_HA",
                    ' %'
                )
            )
            """
        va_manager.set_display_expression(display_expression)

        # VA_ESS
        field_name = "VA_ESS"
        va_f.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        config = {
            'FilterExpression': '"variation" IS NULL',
            'Key': 'fid',
            'LayerName': self.essences_layer.name(),
            'Value': 'essence_variation'
        }
        va_f.add_value_relation(field_name, config)

        # VA_TX_HA
        field_name = "VA_TX_HA"
        va_f.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        expression = '"VA_CUMUL_TX_VA" + "VA_TX_HA" = 100'
        description = 'La somme de VA_TX_HA et de VA_CUMUL_TX_VA doit être égale à 100.'
        va_f.set_constraint_expression(field_name, expression, description)
        va_f.add_range(field_name, {'AllowNull': False, 'Max': 100, 'Min': 0, 'Precision': 0, 'Step': 10})

        # CUMUL_TX_VA
        field_name = "VA_CUMUL_TX_VA"
        default_value = """aggregate(layer:='Va', aggregate:='sum', expression:="VA_TX_HA", filter:="UUID" = attribute(@parent, 'UUID'))"""
        va_f.set_default_value(field_name, default_value)
        va_f.set_read_only(field_name)