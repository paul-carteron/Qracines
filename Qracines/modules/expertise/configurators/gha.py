from qgis.core import QgsFieldConstraints

from ....core.layer import FormBuilder, FieldEditor
from ....utils.essence import configure_essence_field

class GhaConfigurator:

    def __init__(self, layer, essences):
        self.layer = layer
        self.essences = essences

        self.fb = FormBuilder(layer)
        self.fe = FieldEditor(layer)

    def configure(self):

        print("configure GHA layer")

        self._init_form()
        self._configure_fields()
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

        # region GHA_ESSENCE_ID - GHA_ESSENCE_SECONDAIRE_ID
        field_ess = "GHA_ESSENCE_ID"
        field_ess2 = "GHA_ESSENCE_SECONDAIRE_ID"
        
        config = {
            'Key': 'fid',
            'Layer': self.essences.id(),
            'Value': 'essence_variation',
            'AllowNull': True,
            'FilterExpression': '"selected" = true AND "variation" IS NULL'
        }

        self.fe.add_value_relation(field_ess, config)

        config = {
            'Key': 'fid',
            'Layer': self.essences.id(),
            'Value': 'essence_variation',
            'AllowNull': True,
            'FilterExpression': '("selected" = false OR "selected" IS NULL) AND "variation" IS NULL'
        }

        self.fe.add_value_relation(field_ess2, config)

        expr = f'''(COALESCE("{field_ess}", '') <> '') != (COALESCE("{field_ess2}", '') <> '')'''
        msg = "Veuillez sélectionner une valeur pour ESSENCE ou ESSENCE_SECONDAIRE (mais pas les deux)."
        self.fe.set_constraint_expression(field_ess, expr, msg, QgsFieldConstraints.ConstraintStrengthHard)
        # endregion

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


    def _set_qfield_properties(self):
        treshold = 20
        self.layer.setCustomProperty(
            "QFieldSync/value_map_button_interface_threshold",
            treshold
        )
