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
        placette_manager.layer.setCustomProperty("QFieldSync/value_map_button_interface_threshold", 4)

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

        return None
