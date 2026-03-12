from .....core.layer.manager import FormBuilder, FieldEditor
from .....utils.essence import configure_essence_field


class TseConfigurator:

    def __init__(self, layer, essences, codes):
        self.layer = layer
        self.essences = essences
        self.codes = codes

        self.fb = FormBuilder(layer)
        self.fe = FieldEditor(layer)

    def configure(self):

        print("configure TAILLIS layer")

        self._init_form()
        self._configure_fields()
        self._configure_essence()
        self._set_qfield_properties()

    def _init_form(self):

        self.fb.init_form()
        self.fb.new_add_fields(["TSE_ESSENCE_ID", "TSE_ESSENCE_SECONDAIRE_ID"])
        self.fb.apply()

    def _configure_fields(self):

        # ALIASES
        aliases = [
            ("TSE_ESSENCE_ID", "Essence"),
            ("TSE_ESSENCE_SECONDAIRE_ID", "Autre essence")
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
                    coalesce(NULLIF("TSE_ESSENCE_ID", ''), "TSE_ESSENCE_SECONDAIRE_ID")
                ),
                attribute(@ess, 'essence_variation')
            )
            """
        self.layer.setDisplayExpression(display_expression)

    def _configure_essence(self):

        configure_essence_field(
            self.layer,
            "TSE_ESSENCE_ID",
            "TSE_ESSENCE_SECONDAIRE_ID",
            self.essences,
            self.codes,
            with_variation=False
        )

    def _set_qfield_properties(self):
        
        self.layer.setCustomProperty(
            "QFieldSync/value_map_button_interface_threshold",
            len(self.codes) + 1
        )