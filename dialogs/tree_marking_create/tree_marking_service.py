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

from ...core.layer_factory import LayerFactory
from ...core.layer.manager import LayerManager
from ...utils.layers import load_gpkg
from ...utils.utils import replier


class TreeMarkingService:

    def __init__(
        self,
        codes: list,
        dmin: int,
        dmax: int,
        hmin: int,
        hmax: int,
        essences_layer,
    ):
        self.iface = iface
        self.project = QgsProject.instance()
        self.root = self.project.layerTreeRoot()
        self.codes = codes
        self.dmin, self.dmax = dmin, dmax
        self.hmin, self.hmax = hmin, hmax
        self.essences_layer = essences_layer

    def run(self):
        """
        Runs the full workflow. 
        Returns the output_dir path (as str) if packaging was done, otherwise None.
        Raises on any error.
        """
        self._create_and_load_gpkg()

        arbres_manager = LayerManager("arbres")
        essences_manager = LayerManager("essences")

        self._init_form(arbres_manager)

        self._configure_essence_field(arbres_manager, essences_manager, self.codes)
        self._configure_aliases(arbres_manager)
        self._configure_fid(arbres_manager)
        self._configure_uuid(arbres_manager)
        self._configure_compteur(arbres_manager)
        self._configure_parcelle(arbres_manager)
        self._configure_diametre(arbres_manager, self.dmin, self.dmax)
        self._configure_hauteur(arbres_manager, self.hmin, self.hmax)
        self._configure_effectif(arbres_manager)
        self._configure_observation(arbres_manager)
        self._configure_favori(arbres_manager)
        self._configure_fid_code(arbres_manager)
        self._configure_labelling(arbres_manager)

        replier()

        arbres_manager.layer.setCustomProperty("QFieldSync/value_map_button_interface_threshold", 99)

    def _create_and_load_gpkg(self):
        layers = [
            LayerFactory.create("arbres", "INVENTAIRE"),
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
        load_gpkg(self.gpkg_path, group_name="INVENTAIRE")

    @staticmethod
    def _init_form(arbres_manager):
        arbre_f = arbres_manager.forms

        arbre_f.init_drag_and_drop_form()
        arbre_f.add_fields("COMPTEUR")
        arbre_f.add_fields("LOT", "PARCELLE", name="Localisation" ,columns=2)
        arbre_f.add_fields("ESSENCE_ID", "ESSENCE_SECONDAIRE_ID", "DIAMETRE", "HAUTEUR", "EFFECTIF", "OBSERVATION", "FAVORI", "ID_CODE")
    
    @staticmethod
    def _configure_essence_field(arbres_manager, essences_manager, codes):
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
    def _configure_aliases(layer_manager):
        aliases = [
            ("ID_CODE", "CODE"),
            ("ESSENCE_ID", "ESSENCE"),
            ("ESSENCE_SECONDAIRE_ID", "ESSENCE SECONDAIRE"),
            ("FAVORI", "⭐"),
            ("COMPTEUR", "ID")]
        
        for field, alias in aliases:
            layer_manager.fields.set_alias(field, alias)

    @staticmethod
    def _configure_fid(layer_manager):
        layer_manager.fields.set_default_value("fid", 'if (maximum("fid") is NULL, 1 ,maximum("fid") + 1)')

    @staticmethod
    def _configure_uuid(layer_manager):
        field_name = "UUID"
        layer_manager.fields.set_constraint(field_name, QgsFieldConstraints.ConstraintUnique)
        layer_manager.fields.set_default_value(field_name, "uuid()")
        layer_manager.fields.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)

    @staticmethod
    def _configure_compteur(layer_manager):
        field_name = "COMPTEUR"
        layer_manager.fields.set_read_only(field_name)
        layer_manager.fields.set_default_value(field_name, 'count("fid") + 1')

    @staticmethod
    def _configure_parcelle(layer_manager):
        field_name = "PARCELLE"
        layer_manager.fields.set_reuse_last_value(field_name)
        layer_manager.fields.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)

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

