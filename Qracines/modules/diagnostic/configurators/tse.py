from qgis.core import QgsFieldConstraints
from ....core.layer import FormBuilder, FieldEditor

class TseConfigurator:

    def __init__(self, layer, essences):
        self.layer = layer
        self.essences = essences
        self.fb = FormBuilder(layer)
        self.fe = FieldEditor(layer)

    def configure(self):
        print("configure TSE layer")
        self._init_form()
        self._configure_fields()

    def _init_form(self):
        self.fb.init_form()
        self.fb.new_add_fields(["TSE_ESS", "TSE_DIM"])
        self.fb.apply()

    def _configure_fields(self):
        
        # ALIASES
        aliases = [
            ("TSE_ESS", "Essence Taillis"),
            ("TSE_DIM", "Dimension"),
        ]
        
        for field, alias in aliases:
            self.fe.set_alias(field, alias)

        # DISPLAY EXPRESSION
        ess_layer_name = self.essences.name()
        display_expression = f"""
            WITH_VARIABLE(
                'ess',
                get_feature('{ess_layer_name}', 'fid', "TSE_ESS"),
                concat(attribute(@ess, 'essence_variation'), ' : ', "TSE_DIM")
            )
            """
        self.layer.setDisplayExpression(display_expression)

        # TSE_ESS
        field_name = "TSE_ESS"
        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        config = {
            'FilterExpression': '"variation" IS NULL',
            'Key': 'fid',
            'LayerName': self.essences.name(),
            'Value': 'essence_variation'
        }
        self.fe.add_value_relation(field_name, config)

        # TSE_DIM
        tse_dim = {
                '<5': '<5 cm',
                '5-15': '5-15 cm',
                '10-30': '10-30 cm',
                '25-45': '25-45 cm',
                '>40': '>40 cm'
            }
        self.fe.add_value_map('TSE_DIM', {'map': [{str(name): str(code)} for code, name in tse_dim.items()]})
