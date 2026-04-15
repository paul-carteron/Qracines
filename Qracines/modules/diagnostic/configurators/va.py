from qgis.core import QgsFieldConstraints

from ....core.layer import FormBuilder, FieldEditor

class VaConfigurator:

    def __init__(self, layer, essences):

        self.layer = layer
        self.essences = essences

        self.fb = FormBuilder(layer)
        self.fe = FieldEditor(layer)

    def configure(self):

        print("configure VA layer")
        self._init_form()
        self._configure_fields()
      
    def _init_form(self):
        self.fb.init_form()
        self.fb.new_add_fields(["VA_ESS", "VA_TX_HA", "VA_CUMUL_TX_VA"])
        self.fb.apply()

    def _configure_fields(self):
        
        # ALIASES
        aliases = [
            ("VA_ESS", "Essence Plant/Régé"),
            ("VA_TX_HA", "Proportion [1 ess => 100%]"),
            ("VA_CUMUL_TX_VA", "Cumul des recouvrements"),
        ]
        
        for field, alias in aliases:
            self.fe.set_alias(field, alias)
        
        # DISPLAY EXPRESSION
        ess_layer_name = self.essences.name()
        display_expression = f"""
            WITH_VARIABLE(
                'ess',
                get_feature('{ess_layer_name}', 'fid', "VA_ESS"),
                concat(
                    attribute(@ess, 'essence_variation'),
                    ' : ',
                    "VA_TX_HA",
                    ' %'
                )
            )
            """
        self.layer.setDisplayExpression(display_expression)

        # VA_ESS
        field_name = "VA_ESS"
        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        config = {
            'FilterExpression': '"variation" IS NULL',
            'Key': 'fid',
            'LayerName': self.essences.name(),
            'Value': 'essence_variation'
        }
        self.fe.add_value_relation(field_name, config)

        # VA_TX_HA
        field_name = "VA_TX_HA"
        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        expression = '"VA_CUMUL_TX_VA" + "VA_TX_HA" = 100'
        description = 'La somme de VA_TX_HA et de VA_CUMUL_TX_VA doit être égale à 100.'
        self.fe.set_constraint_expression(field_name, expression, description)
        self.fe.add_range(field_name, {'AllowNull': False, 'Max': 100, 'Min': 0, 'Precision': 0, 'Step': 10})

        # CUMUL_TX_VA
        field_name = "VA_CUMUL_TX_VA"
        default_value = """aggregate(layer:='Va', aggregate:='sum', expression:="VA_TX_HA", filter:="UUID" = attribute(@parent, 'UUID'))"""
        self.fe.set_default_value(field_name, default_value)
        self.fe.set_read_only(field_name)