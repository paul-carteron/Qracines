from qgis.core import QgsFieldConstraints

from .....core.layer.manager import FormBuilder, FieldEditor
from .....utils.essence import configure_essence_field


class VaConfigurator:

    def __init__(self, layer, essences, codes):
        self.layer = layer
        self.essences = essences
        self.codes = codes

        self.fb = FormBuilder(layer)
        self.fe = FieldEditor(layer)

    def configure(self):

        print("configure VALEUR AVENIR layer")

        self._init_form()
        self._configure_fields()
        self._configure_essence()
        self._set_qfield_properties()

    def _init_form(self):

        self.fb.init_form()

        self.fb.new_add_fields([
            "VA_ESSENCE_ID",
            "VA_ESSENCE_SECONDAIRE_ID",
            "VA_TX_TROUEE",
            "VA_AGE_APP",
            "VA_TX_HA",
            "CUMUL_TX_VA"
        ])

        self.fb.apply()

    def _configure_fields(self):

        # ALIASES
        aliases = [
            ("VA_ESSENCE_ID", "Essence"),
            ("VA_ESSENCE_SECONDAIRE_ID", "Autre essence"),
            ("VA_AGE_APP", "Age Apparent"),
            ("VA_TX_TROUEE", "Taux trouée [%]"),
            ("VA_TX_HA", "Recouvrement [%]"),
            ("CUMUL_TX_VA", "Cumul des recouvrements"),
        ]
        
        for field, alias in aliases:
            self.fe.set_alias(field, alias)
        
        # DISPLAY EXPRESSION
        ess_layer_name = self.essences.name()
        display_expression = f"""
            WITH_VARIABLE(
                'ess',
                get_feature(
                    '{ess_layer_name}',
                    'fid',
                    coalesce(NULLIF("VA_ESSENCE_ID", ''), "VA_ESSENCE_SECONDAIRE_ID")
                ),
                concat(
                    attribute(@ess, 'essence_variation'),
                    ' : ',
                    "VA_TX_HA",
                    ' %'
                )
            )
            """
        self.layer.setDisplayExpression(display_expression)

        # VA_AGE_APP
        field_name = "VA_AGE_APP"
        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        self.fe.set_constraint_expression(field_name, f'"{field_name}" > 0', "L'âge doit être supérieur à 0", strength=QgsFieldConstraints.ConstraintStrengthHard)
        self.fe.add_range(field_name, {'AllowNull': False, 'Max': 300, 'Min': 0, 'Precision': 0, 'Step': 1})

        # VA_TX_TROUEE
        self.fe.add_range("VA_TX_TROUEE", {'AllowNull': True, 'Max': 100, 'Min': 0, 'Precision': 0, 'Step': 10})

        # VA_TX_HA
        field_name = "VA_TX_HA"
        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        expression = '"CUMUL_TX_VA" + "VA_TX_HA" = 100'
        description = 'La somme de VA_TX_HA et de CUMUL_TX_VA doit être égale à 100.'
        self.fe.set_constraint_expression(field_name, expression, description)
        self.fe.add_range(field_name, {'AllowNull': False, 'Max': 100, 'Min': 0, 'Precision': 0, 'Step': 10})

        # CUMUL_TX_VA
        field_name = "CUMUL_TX_VA"
        default_value = """aggregate(layer:='va', aggregate:='sum', expression:="VA_TX_HA", filter:="UUID" = attribute(@parent, 'UUID'))"""
        self.fe.set_default_value(field_name, default_value)
        self.fe.set_read_only(field_name)

    def _configure_essence(self):

        configure_essence_field(
            self.layer,
            "VA_ESSENCE_ID",
            "VA_ESSENCE_SECONDAIRE_ID",
            self.essences,
            self.codes,
            with_variation=False
        )

    def _set_qfield_properties(self):
        self.layer.setCustomProperty(
            "QFieldSync/value_map_button_interface_threshold",
            len(self.codes) + 1
        )