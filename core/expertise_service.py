from pathlib import Path
import processing

from qgis.core import (
    QgsProject,
    QgsProcessing,
    QgsFieldConstraints,
    QgsFeatureRequest,
    QgsExpression,
    QgsPalLayerSettings,
    QgsTextFormat,
    QgsVectorLayerSimpleLabeling
)

from qgis.utils import iface

from PyQt5.QtCore import QVariant
from PyQt5.QtGui import QFont

from ..core.layer_factory import LayerFactory
from ..core.db.manager import DatabaseManager
from ..core.layer.manager import LayerManager
from ..utils.path_manager import get_peuplements
from ..utils.layer_utils import add_layers_from_gpkg, create_relation
from ..utils.qfield_utils import package_for_qfield
from ..utils.variable_utils import get_project_variable


class ExpertiseService:

    def __init__(
        self,
        output_dir: Path,
        package_for_qfield: bool,
        codes: list,
        codes_taillis: list,
        dmin: int,
        dmax: int,
        hmin: int,
        hmax: int,
        essences_layer: dict
    ):
        self.iface = iface
        self.project = QgsProject.instance()
        self.root = self.project.layerTreeRoot()
        self.output_dir = output_dir
        self.package_for_qfield = package_for_qfield
        self.codes = codes,
        self.codes_taills = codes_taillis,
        self.dmin, self.dmax = dmin, dmax
        self.hmin, self.hmax = hmin, hmax
        self.essences_layer = essences_layer

    def run_full_diagnostic(self):
        """
        Runs the full workflow. 
        Returns the output_dir path (as str) if packaging was done, otherwise None.
        Raises on any error.
        """
        self._create_and_load_gpkg()

        placette_manager = LayerManager("placette")
        self._create_relations()
        self._init_form(placette_manager)
        self._configure_placette(placette_manager)

        # Run packaging if needed
        if self.package_for_qfield:
            self._package_for_qfield()
            # signal back that packaging happened
            return str(self.output_dir)
        return None

    def _create_and_load_gpkg(self):

        layers = [
            LayerFactory.create("placette", "EXPERTISE"),
            LayerFactory.create("transect", "EXPERTISE"),
            LayerFactory.create("gha", "EXPERTISE"),
            LayerFactory.create("tse", "EXPERTISE"),
            LayerFactory.create("reg", "EXPERTISE"),
            LayerFactory.create("va_ess", "EXPERTISE"),
            self.essences_layer
        ]

        result = processing.run("native:package", {
            'LAYERS':      layers,
            'OUTPUT':      QgsProcessing.TEMPORARY_OUTPUT,
            'OVERWRITE':   True,
            'SAVE_STYLES': False
        })

        self.gpkg_path = result['OUTPUT']

        # 5) load it back into the project
        add_layers_from_gpkg(self.gpkg_path)

    def _create_relations(self):
        pairs = [
            ('placette', 'gha'),
            ('placette', 'tse'),
            ('placette', 'reg'),
            ('placette', 'va_ess')
        ]
        for parent, child in pairs:
            create_relation(
                parent_name = parent, child_name = child,
                parent_field = 'UUID', child_field = 'UUID',
                relation_id = f'{parent}_{child}',
                relation_name = child
            )
    
    @staticmethod
    def _init_form(placette_manager):
        placette_manager.forms.init_drag_and_drop_form()
        placette_manager.forms.add_fields_to_tab("fid")
        placette_manager.forms.add_fields_to_tab("PLTM_PARCELLE", "PLTM_STRATE", tab_name="Localisation", columns=2)
        placette_manager.forms.add_fields_to_tab("PLTM_TYPE")

        # ve: stand for visibility_expression
        gha_ve = """left("PLTM_TYPE",2)='FR' OR left("PLTM_TYPE",2)='FI' OR left("PLTM_TYPE",2)='MF' OR left("PLTM_TYPE",2)='PE'"""
        tse_ve = """"PLTM_TYPE"<>''"""
        reg_ve = """"PLTM_TYPE"<>''"""
        va_ve = """left("PLTM_TYPE",2)='FR' OR left("PLTM_TYPE",2)='FI' OR left("PLTM_TYPE",2)='PE'"""

        placette_manager.forms.add_relation_to_tab("gha", tab_name="Surface terrière", visibility_expression = gha_ve)
        placette_manager.forms.add_relation_to_tab("tse", tab_name="Taillis", visibility_expression = tse_ve)
        placette_manager.forms.add_fields_to_tab("VA_TX_TROUEE", tab_name="Valeur d'avenir", visibility_expression = reg_ve)
        placette_manager.forms.add_relation_to_tab("va_ess", tab_name="Valeur d'avenir")
        placette_manager.forms.add_relation_to_tab("reg", tab_name="Régénération", visibility_expression = va_ve)
    
    @staticmethod
    def _configure_placette(placette_manager):
        # ALIASES
        aliases = [
            ("fid", "Placette"),
            ("PLTM_PARCELLE", "Parcelle"),
            ("PLTM_STRATE", "Strate"),
            ("PLTM_TYPE", "Type de peuplement"),
            ("VA_TX_TROUEE", "Taux trouée [%]")]
        
        for field, alias in aliases:
            placette_manager.fields.set_alias(field, alias)

        # FID
        placette_manager.fields.set_default_value("fid", 'if (maximum("fid") is NULL, 1 ,maximum("fid") + 1)')

        # UUID
        field_name = "UUID"
        placette_manager.fields.set_constraint(field_name, QgsFieldConstraints.ConstraintUnique)
        placette_manager.fields.set_default_value(field_name, "uuid()")
        placette_manager.fields.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)

        # PLTM_PARCELLE & PLTM_STRATE
        expression = '"PLTM_PARCELLE" is not NULL OR "PLTM_STRATE" is not NULL'
        description = "Ajouter une parcelle ou une strate si l'inventaire n'utilise pas de carto"
        placette_manager.fields.set_constraint_expression("PLTM_PARCELLE", expression, description)
        placette_manager.fields.set_constraint_expression("PLTM_STRATE", expression, description)

        # PLTM_TYPE
        peuplements = get_peuplements()
        placette_manager.fields.add_value_map('PLTM_TYPE', {'map': [{str(name): str(code)} for code, name in peuplements.items()]})

        # VA_TX_TROUEE
        placette_manager.fields.add_range("VA_TX_TROUEE", {'AllowNull': True, 'Max': 100, 'Min': 0, 'Precision': 0, 'Step': 10})


    @staticmethod
    def _configure_essence_field( arbres_manager, essences_manager, codes):
        # 1. Build value map for main ESSENCE_ID field
        query_string = " OR ".join([f"code = '{code}'" for code in codes])
        request = QgsFeatureRequest(QgsExpression(query_string))

        essences_list = [
            {f"{ess['code']}{' ' + ess['variation'] if ess['variation'] else ''}": ess['fid']}
            for ess in essences_manager.layer.getFeatures(request)
        ]
        arbres_manager.fields.add_value_map('ESSENCE_ID', {'map': essences_list})

        # 2. Ensure "selected" field for secondary essences
        if "selected" not in [f.name() for f in essences_manager.layer.fields()]:
            essences_manager.fields.add_field("selected", QVariant.Bool)

        # 3. Mark secondary essences as selected
        excluded_codes = ", ".join([f"'{code}'" for code in codes])
        expression = f"code NOT IN ({excluded_codes})"
        essences_manager.fields.set_field_value_by_expression("selected", True, expression)

        # 4. Add value relation for ESSENCE_SECONDAIRE_ID
        config = {
            'FilterExpression': '"selected" = True',
            'Key': 'fid',
            'Layer': essences_manager.layer.id(),
            'Value': 'essence_variation',
            'AllowNull': True
        }
        arbres_manager.fields.add_value_relation('ESSENCE_SECONDAIRE_ID', config)

        # 5. Constrain ESSENCE_ID & ESSENCE_SECONDAIRE_ID
        ess_expr = """
        ((COALESCE("ESSENCE_ID", '') <> '') AND "ESSENCE_SECONDAIRE_ID" IS NULL)
        OR
        ((COALESCE("ESSENCE_ID", '') = '') AND "ESSENCE_SECONDAIRE_ID" IS NOT NULL)
        """
        msg = "Veuillez sélectionner une valeur pour ESSENCE ou ESSENCE_SECONDAIRE (mais pas les deux)."
        arbres_manager.fields.set_constraint_expression('ESSENCE_ID', ess_expr, msg, QgsFieldConstraints.ConstraintStrengthHard)



    @staticmethod
    def _configure_diametre(layer_manager, dmin, dmax):
        field_name = "DIAMETRE"
        layer_manager.fields.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        layer_manager.fields.add_value_map(field_name, {'map': [{str(d): str(d)} for d in range(dmin, dmax + 1, 5)]})
        layer_manager.fields.set_constraint_expression(
            field_name,
            '"DIAMETRE" != \'\'',
            "Le champ DIAMETRE ne peut pas être vide.", 
            QgsFieldConstraints.ConstraintStrengthHard
            )

    @staticmethod
    def _configure_hauteur(layer_manager, hmin, hmax):
        field_name = "HAUTEUR"
        layer_manager.fields.add_value_map(field_name, {'map': [{str(h): str(h)} for h in range(hmin, hmax + 1)]})

    @staticmethod
    def _configure_effectif(layer_manager):
        field_name = "EFFECTIF"
        layer_manager.fields.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        layer_manager.fields.add_range('EFFECTIF', {'AllowNull': False, 'Max': 1000, 'Min': 0, 'Precision': 0, 'Step': 1})
        layer_manager.fields.set_default_value("EFFECTIF", '1', False)

    @staticmethod
    def _configure_observation(layer_manager):
        field_name = "OBSERVATION"
        observation_choices = ["Chablis", "Bio", "Ehouppé", "Cablage"]
        layer_manager.fields.add_value_map(field_name, {'map': [{v: v} for v in observation_choices]})

    @staticmethod
    def _configure_favori(layer_manager):
        layer_manager.fields.set_default_value("FAVORI", "FALSE")

    @staticmethod
    def _configure_fid_code(layer_manager):
        field_name = "ID_CODE"
        layer_manager.fields.set_read_only(field_name)
        layer_manager.fields.set_default_value(
            field_name,
            """
            WITH_VARIABLE(
                'ess',
                get_feature(
                    'essences',
                    'fid',
                    coalesce(NULLIF("ESSENCE_ID", ''), "ESSENCE_SECONDAIRE_ID")
                ),
                concat(
                    "COMPTEUR",
                    ': ',
                    attribute(@ess, 'code'),
                    CASE
                        WHEN attribute(@ess, 'variation') IS NOT NULL
                        THEN concat(' ', attribute(@ess, 'variation'))
                        ELSE ''
                    END,
                    ' D', "DIAMETRE",
                    CASE
                        WHEN "HAUTEUR" IS NOT NULL AND "HAUTEUR" != ''
                        THEN concat(' H', "HAUTEUR")
                        ELSE ''
                    END
                )
            )
            """
        )

    @staticmethod
    def _configure_labelling(arbres_manager):
        label_settings = QgsPalLayerSettings()
        label_settings.fieldName = "COMPTEUR"
        text_format = QgsTextFormat()
        text_format.setFont(QFont("Arial", 12))
        text_format.setSize(12)
        label_settings.setFormat(text_format)
        labeling = QgsVectorLayerSimpleLabeling(label_settings)
        arbres_manager.layer.setLabeling(labeling)
        arbres_manager.layer.setLabelsEnabled(True)
        arbres_manager.layer.triggerRepaint()

    def _package_for_qfield(self):
        forest_prefix = get_project_variable("forest_prefix")
        codes = "_".join(self.codes)
        filename = f"{forest_prefix}_D{self.dmax}H{self.hmax}_{codes}" if forest_prefix else f"D{self.dmax}H{self.hmax}_{codes}"
        
        package_for_qfield(iface, self.project, self.output_dir, filename)

