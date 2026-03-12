from qgis.core import QgsFieldConstraints

from ....core.layer.manager import FormBuilder, FieldEditor
from ....utils.essence import configure_essence_field

class GhaConfigurator:

    def __init__(self, layer, essences, codes):
        self.layer = layer
        self.essences = essences
        self.codes = codes

        self.fb = FormBuilder(layer)
        self.fe = FieldEditor(layer)

    def configure(self):

        print("configure GHA layer")

        self._init_form()
        self._configure_fields()
        self._configure_essence()
        self._set_qfield_properties()

    def _init_form(self):

        self.fb.init_form()
        self.fb.new_add_fields(["GHA_ESSENCE_ID", "GHA_ESSENCE_SECONDAIRE_ID", "GHA_G"])
        self.fb.apply()

    def _configure_fields(self):

        aliases = [
            ("GHA_ESSENCE_ID", "Essence"),
            ("GHA_ESSENCE_SECONDAIRE_ID", "Autre essence"),
            ("GHA_G", "Surface terrière")
        ]
        
        for field, alias in aliases:
            self.fe.set_alias(field, alias)
        
        # GHA_G
        field_name = "GHA_G"
        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        self.fe.set_constraint_expression(field_name, f'"{field_name}" > 0', "La surface terrière doit être supérieur à 0", strength=QgsFieldConstraints.ConstraintStrengthHard)
        self.fe.add_range(field_name, {'AllowNull': False, 'Max': 100, 'Min': 0, 'Precision': 0, 'Step': 1})

        # DISPLAY EXPRESSION
        ess_layer_name = self.essences.name()
        display_expression = f"""
            WITH_VARIABLE(
                'ess',
                get_feature(
                    '{ess_layer_name}',
                    'fid',
                    coalesce(NULLIF("GHA_ESSENCE_ID", ''), "GHA_ESSENCE_SECONDAIRE_ID")
                ),
                concat(attribute(@ess, 'essence_variation'),
                ' : ',
                "GHA_G",
                ' m²/ha ')
            )
            """
        self.layer.setDisplayExpression(display_expression)

    def _configure_essence(self):

        configure_essence_field(
            self.layer,
            "GHA_ESSENCE_ID",
            "GHA_ESSENCE_SECONDAIRE_ID",
            self.essences,
            self.codes,
            with_variation=False
        )

    def _set_qfield_properties(self):
        self.layer.setCustomProperty(
            "QFieldSync/value_map_button_interface_threshold",
            len(self.codes) + 1
        )
