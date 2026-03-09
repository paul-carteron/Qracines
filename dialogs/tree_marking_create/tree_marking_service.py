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
from ..tree_marking_config import TYPE_CHOICES, MARQUAGE_CHOICES, COULEUR_CHOICES, MARTEAU_CHOICES


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

        param_manager = LayerManager("param")
        arbres_manager = LayerManager("arbres")
        essences_manager = LayerManager("essences")

        self._init_param_form(param_manager)
        self._configure_param(param_manager)

        self._init_arbre_form(arbres_manager)

        self._configure_essence_field(arbres_manager, essences_manager, self.codes)
        self._configure_aliases(arbres_manager)
        self._configure_uuid(arbres_manager)
        self._configure_compteur(arbres_manager)
        self._configure_parcelle(arbres_manager, param_manager)
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
            LayerFactory.create("param", "INVENTAIRE"),
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
    def _init_param_form(param_manager):
        param_f = param_manager.forms

        param_f.init_form() 
        param_f.add_fields("TYPE", "LOT", "PARCELLE", "SURFACE", "MARQUE","MARQUAGE_BO", "COULEUR_BO", "MARQUAGE_BI", "COULEUR_BI", name="Paramétrage")
    
    def _configure_param(self, param_manager):

        aliases = [
            ("TYPE", "Type"),
            ("LOT", "Lot"),
            ("PARCELLE", "Parcelle"),
            ("SURFACE", "Surface [ha]"),
            ("MARQUAGE_BO", "Marquage BO"),
            ("COULEUR_BO", "Couleur BO"),
            ("MARQUAGE_BI", "Marquage BI"),
            ("COULEUR_BI", "Couleur BI"),
            ("MARQUE", "Marque"),
        ]
        
        for field, alias in aliases:
            param_manager.fields.set_alias(field, alias)

        reuse = ["TYPE", "LOT","MARQUAGE_BO", "COULEUR_BO", "MARQUAGE_BI", "COULEUR_BI"]
        for field_name in reuse:
            param_manager.fields.set_reuse_last_value(field_name)

        param_manager.fields.set_constraint("TYPE", QgsFieldConstraints.ConstraintNotNull)
        param_manager.fields.set_constraint("LOT", QgsFieldConstraints.ConstraintNotNull)
        param_manager.fields.set_constraint("PARCELLE", QgsFieldConstraints.ConstraintNotNull)
        param_manager.fields.set_constraint("SURFACE", QgsFieldConstraints.ConstraintNotNull)
        param_manager.fields.add_range("SURFACE", {'AllowNull': False, 'Max': 1000, 'Min': 0, 'Precision': 2, 'Step': 0.01})

        param_manager.fields.add_value_map("TYPE", {'map': [{v: k} for k, v in TYPE_CHOICES.items()]})

        for field_name in ["MARQUAGE_BO", "MARQUAGE_BI"]:
            param_manager.fields.add_value_map(field_name, {'map': [{v: k} for k, v in MARQUAGE_CHOICES.items()]})

        for field_name in ["COULEUR_BO", "COULEUR_BI"]:
            param_manager.fields.add_value_map(field_name, {'map': [{v: k} for k, v in COULEUR_CHOICES.items()]})

        param_manager.fields.add_value_map("MARQUE", {'map': [{v: k} for k, v in MARTEAU_CHOICES.items()]})

    @staticmethod
    def _init_arbre_form(arbres_manager):
        arbre_f = arbres_manager.forms

        arbre_f.init_form()
        
        tab = arbre_f.create_tab("")
        group1 = arbre_f.create_group("", columns=2, parent=tab)
        arbre_f.new_add_fields(["COMPTEUR", "PARCELLE"], parent = group1)
        arbre_f.new_add_fields(["ESSENCE_ID", "ESSENCE_SECONDAIRE_ID", "DIAMETRE", "HAUTEUR", "EFFECTIF", "FAVORI", "OBSERVATION", "ID_CODE"], parent = tab)

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
            ("COMPTEUR", "N°")]
        
        for field, alias in aliases:
            layer_manager.fields.set_alias(field, alias)

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
    def _configure_parcelle(layer_manager, param_manager):
        field_name = "PARCELLE"
        layer_manager.fields.set_reuse_last_value(field_name)
        layer_manager.fields.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        config = {
            'Key': 'PARCELLE',
            'Layer': param_manager.layer.id(),
            'Value': 'PARCELLE',
            'AllowNull': False
        }
        layer_manager.fields.add_value_relation(field_name, config)


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
                    END,
                    CASE
                        WHEN "EFFECTIF" IS NOT NULL
                        THEN concat(' N', "EFFECTIF")
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

