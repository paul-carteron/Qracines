from qgis.core import (
    QgsFieldConstraints,
    QgsPalLayerSettings,
    QgsTextFormat,
    QgsVectorLayerSimpleLabeling,
    QgsTextBufferSettings,
)
from PyQt5.QtGui import QFont, QColor

from ....core.layer import FormBuilder, FieldEditor

class ArbresConfigurator:

    def __init__(self, layer, param, essences, lst_hauteur, lst_diam):
        self.layer = layer
        self.param = param
        self.essences = essences
        self.lst_hauteur = lst_hauteur
        self.lst_diam = lst_diam

        self.fb = FormBuilder(layer)
        self.fe = FieldEditor(layer)

    def configure(self):
        
        self._init_form()
        self._configure_fields()
        self._set_qfield_properties()
        self._style()

    def _init_form(self):
        
        self.fb.init_form()
  
        tab = self.fb.create_tab("")
        group1 = self.fb.create_group("", columns=2, parent=tab)
        self.fb.new_add_fields(["COMPTEUR", "PARCELLE"], parent = group1)
        self.fb.new_add_fields(["ESSENCE_ID", "ESSENCE_SECONDAIRE_ID", "DIAMETRE", "HAUTEUR", "EFFECTIF", "FAVORI", "OBSERVATION", "ID_CODE"], parent = tab)

        self.fb.apply()

    def _configure_fields(self):

        aliases = [
            ("ID_CODE", "CODE"),
            ("ESSENCE_ID", "ESSENCE"),
            ("ESSENCE_SECONDAIRE_ID", "ESSENCE SECONDAIRE"),
            ("FAVORI", "⭐"),
            ("COMPTEUR", "N°")
        ]
        
        for field, alias in aliases:
            self.fe.set_alias(field, alias)

        # region UUID
        field_name = "UUID"
        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintUnique)
        self.fe.set_default_value(field_name, "uuid()")
        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        # endregion

        # region COMPTEUR
        field_name = "COMPTEUR"
        self.fe.set_read_only(field_name)
        self.fe.set_default_value(field_name, 'count("fid") + 1')
        # endregion

        # region PARCELLE
        field_name = "PARCELLE"
        self.fe.set_reuse_last_value(field_name)
        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        config = {
            'Key': 'PARCELLE',
            'Layer': self.param.id(),
            'Value': 'PARCELLE',
            'AllowNull': False
        }
        self.fe.add_value_relation(field_name, config)
        # endregion

        # region ESSENCE_ID - ESSENCE_SECONDAIRE_ID
        field_ess = "ESSENCE_ID"
        field_ess2 = "ESSENCE_SECONDAIRE_ID"
        config = {
            'Key': 'fid',
            'Layer': self.essences.id(),
            'Value': 'essence_variation',
            'AllowNull': True,
            'FilterExpression': '"selected" = true'
        }

        self.fe.add_value_relation(field_ess, config)

        config = {
            'Key': 'fid',
            'Layer': self.essences.id(),
            'Value': 'essence_variation',
            'AllowNull': True,
            'FilterExpression': '"selected" = false OR "selected" IS NULL'
        }

        self.fe.add_value_relation(field_ess2, config)

        expr = f'''(COALESCE("{field_ess}", '') <> '') != (COALESCE("{field_ess2}", '') <> '')'''
        msg = "Veuillez sélectionner une valeur pour ESSENCE ou ESSENCE_SECONDAIRE (mais pas les deux)."
        self.fe.set_constraint_expression(field_ess, expr, msg, QgsFieldConstraints.ConstraintStrengthHard)
        # endregion

        # region DIAMETRE
        field_name = "DIAMETRE"
        config = {
            'Key': 'fid',
            'Layer': self.lst_diam.id(),
            'Value': 'VALEUR',
            'AllowNull': False,
            'FilterExpression': '''
            "VALEUR" >= attribute(get_feature_by_id('Param',1), 'DMIN') 
            AND 
            "VALEUR" <= attribute(get_feature_by_id('Param',1), 'DMAX')
            '''
        }

        self.fe.add_value_relation(field_name, config)

        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        self.fe.set_constraint_expression(field_name,
            f'"{field_name}" != \'\'',
            f"Le champ {field_name} ne peut pas être vide.", 
            QgsFieldConstraints.ConstraintStrengthHard
        )
        # endregion

        # region HAUTEUR
        config = {
            'Key': 'fid',
            'Layer': self.lst_hauteur.id(),
            'Value': 'VALEUR',
            'AllowNull': False,
            'FilterExpression': '''
            "VALEUR" >= attribute(get_feature_by_id('Param',1), 'HMIN') 
            AND 
            "VALEUR" <= attribute(get_feature_by_id('Param',1), 'HMAX')
            '''
        }

        self.fe.add_value_relation("HAUTEUR", config)
        # endregion

        # region EFFECTIF
        field_name = "EFFECTIF"
        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        self.fe.add_range('EFFECTIF', {'AllowNull': False, 'Max': 1000, 'Min': 0, 'Precision': 0, 'Step': 1})
        self.fe.set_default_value("EFFECTIF", '1', False)
        # endregion

        # region OBSERVATION
        field_name = "OBSERVATION"
        observation_choices = ["Chablis", "Bio", "Ehouppé", "Cablage"]
        self.fe.add_value_map(field_name, {'map': [{v: v} for v in observation_choices]})
        # endregion

        # region FAVORI
        self.fe.set_default_value("FAVORI", "FALSE")
        # endregion

        # region ID_CODE
        field_name = "ID_CODE"
        self.fe.set_read_only(field_name)
        self.fe.set_default_value(
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
    # endregion

    def _set_qfield_properties(self):

        threshold = 30

        self.layer.setCustomProperty(
            "QFieldSync/value_map_button_interface_threshold",
            threshold
        )
        
    def _style(self):
        label_settings = QgsPalLayerSettings()
        label_settings.fieldName = "COMPTEUR"

        text_format = QgsTextFormat()
        text_format.setFont(QFont("Arial", 12))
        text_format.setSize(12)

        buffer = QgsTextBufferSettings()
        buffer.setEnabled(True)
        buffer.setSize(1.5)  # thickness
        buffer.setColor(QColor("white"))

        text_format.setBuffer(buffer)   

        label_settings.setFormat(text_format)

        labeling = QgsVectorLayerSimpleLabeling(label_settings)
        self.layer.setLabeling(labeling)
        self.layer.setLabelsEnabled(True)
        self.layer.triggerRepaint()
