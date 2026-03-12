from qgis.core import (
    QgsFieldConstraints,
    QgsPalLayerSettings,
    QgsTextFormat,
    QgsVectorLayerSimpleLabeling
)
from PyQt5.QtGui import QFont

from ....core.layer import FormBuilder, FieldEditor
from ....utils.essence import configure_essence_field

class ArbresConfigurator:

    def __init__(self, layer, param, dendro, essences, codes):
        self.layer = layer
        self.param = param
        self.dendro = dendro
        self.essences = essences
        self.codes = codes

        self.fb = FormBuilder(layer)
        self.fe = FieldEditor(layer)

    def configure(self):
        
        self._init_form()
        self._configure_fields()
        self._configure_essence()
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
            ("COMPTEUR", "N°")]
        
        for field, alias in aliases:
            self.fe.set_alias(field, alias)

        # UUID
        field_name = "UUID"
        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintUnique)
        self.fe.set_default_value(field_name, "uuid()")
        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)

        # COMPTEUR
        field_name = "COMPTEUR"
        self.fe.set_read_only(field_name)
        self.fe.set_default_value(field_name, 'count("fid") + 1')

        # PARCELLE
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

        # DIAMETRE
        field_name = "DIAMETRE"
        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        dmin = self.dendro["dmin"]
        dmax = self.dendro["dmax"]
        self.fe.add_value_map(field_name, {'map': [{str(d): str(d)} for d in range(dmin, dmax + 1, 5)]})
        self.fe.set_constraint_expression(
            field_name,
            '"DIAMETRE" != \'\'',
            "Le champ DIAMETRE ne peut pas être vide.", 
            QgsFieldConstraints.ConstraintStrengthHard
            )

        # HAUTEUR
        field_name = "HAUTEUR"
        hmin = self.dendro["hmin"]
        hmax = self.dendro["hmax"]
        self.fe.add_value_map(field_name, {'map': [{str(h): str(h)} for h in range(hmin, hmax + 1)]})

        # EFFECTIF
        field_name = "EFFECTIF"
        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        self.fe.add_range('EFFECTIF', {'AllowNull': False, 'Max': 1000, 'Min': 0, 'Precision': 0, 'Step': 1})
        self.fe.set_default_value("EFFECTIF", '1', False)

        # OBSERVATION
        field_name = "OBSERVATION"
        observation_choices = ["Chablis", "Bio", "Ehouppé", "Cablage"]
        self.fe.add_value_map(field_name, {'map': [{v: v} for v in observation_choices]})

        # FAVORI
        self.fe.set_default_value("FAVORI", "FALSE")

        # ID_CODE
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

    def _configure_essence(self):

        configure_essence_field(
            self.layer,
            "ESSENCE_ID",
            "ESSENCE_SECONDAIRE_ID",
            self.essences,
            self.codes,
            with_variation=True
        )

    def _set_qfield_properties(self):

        threshold = max(
            self.dendro["hmax"] + 1,
            (self.dendro["dmax"] + 1) / 5
        )

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
        label_settings.setFormat(text_format)
        labeling = QgsVectorLayerSimpleLabeling(label_settings)
        self.layer.setLabeling(labeling)
        self.layer.setLabelsEnabled(True)
        self.layer.triggerRepaint()

