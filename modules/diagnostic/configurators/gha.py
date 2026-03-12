from qgis.core import QgsFieldConstraints
from .....core.layer.manager import FormBuilder, FieldEditor

class GhaConfigurator:

    def __init__(self, layer, essence_layer):
        self.layer = layer
        self.essences = essence_layer
        self.fb = FormBuilder(layer)
        self.fe = FieldEditor(layer)

    def configure(self):
        print("configure GHA layer")
        self._init_form()
        self._configure_fields()

    def _init_form(self):
        self.fb.init_form()
        self.fb.new_add_fields(["GHA_ESS", "GHA_G"])
        self.fb.apply()
    
    def _configure_fields(self):
        # ALIASES
        aliases = [
            ("GHA_ESS", "Essence Gha"),
            ("GHA_G", "Surface terrière")
        ]
        
        for field, alias in aliases:
            self.fe.set_alias(field, alias)
        
        # DISPLAY EXPRESSION
        ess_layer_name = self.essences.name()
        display_expression = f"""
            WITH_VARIABLE(
                'ess',
                get_feature('{ess_layer_name}', 'fid', "GHA_ESS"),
                concat(
                    attribute(@ess, 'essence_variation'),
                    ' : ',
                    "GHA_G",
                    ' m²/ha '
                )
            )
            """
        self.layer.setDisplayExpression(display_expression)

        # GHA_ESS
        field_name = "GHA_ESS"
        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        config = {
            'FilterExpression': '"variation" IS NULL',
            'Key': 'fid',
            'LayerName': self.essences.name(),
            'Value': 'essence_variation'
        }
        self.fe.add_value_relation(field_name, config)

        # GHA_G
        field_name = "GHA_G"
        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        self.fe.set_constraint_expression(field_name, f'"{field_name}" > 0', "La surface terrière doit être supérieur à 0", strength=QgsFieldConstraints.ConstraintStrengthHard)
        self.fe.set_default_value(field_name, '1', False)
        self.fe.add_range(field_name, {'AllowNull': False, 'Max': 100, 'Min': 0, 'Precision': 0, 'Step': 1})