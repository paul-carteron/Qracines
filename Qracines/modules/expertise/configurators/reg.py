from ....core.layer import FormBuilder, FieldEditor
from ....utils.essence import configure_essence_field


class RegConfigurator:

    def __init__(self, layer, essences, codes):
        self.layer = layer
        self.essences = essences
        self.codes = codes

        self.fb = FormBuilder(layer)
        self.fe = FieldEditor(layer)

    def configure(self):

        print("configure REGENERATION layer")

        self._init_form()
        self._configure_fields()
        self._configure_essence()
        self._set_qfield_properties()

    def _init_form(self):

        self.fb.init_form()

        self.fb.new_add_fields([
            "REG_ESSENCE_ID",
            "REG_ESSENCE_SECONDAIRE_ID",
            "REG_STADE",
            "REG_ETAT"
        ])

        self.fb.apply()

    def _configure_fields(self):

        # ALIASES
        aliases = [
            ("REG_ESSENCE_ID", "Essence"),
            ("REG_ESSENCE_SECONDAIRE_ID", "Autre essence"),
            ("REG_STADE", "Stade"),
            ("REG_ETAT", "Etat"),
        ]
        
        for field, alias in aliases:
            self.fe.set_alias(field, alias)

        # REG_STADE
        stades = {
            "semis_inf_05": "Semis <0.5m",
            "semis_05_1": "Semis 0.5-1m",
            "fourre_1_3": "Fourré 1-3m",
            "semis_3_5": "Gaulis 3-5m",
            "semis_5_15": "Perchis 5m-15cm"
            }
        self.fe.add_value_map('REG_STADE', {'map': [{str(value): str(descr)} for descr, value in stades.items()]}, allow_null=True)

        # REG_ETAT
        etats = {
            "continue_sup_80": "Continue >80%",
            "conseqente_50_80": "Conséquente 50-80%",
            "moderee_30_50": "Modérée 30-50%",
            "eparse_10_30": "Eparse 10-30%",
            "infime_inf_10": "Infime <10%"
            }
        self.fe.add_value_map('REG_ETAT', {'map': [{str(value): str(descr)} for descr, value in etats.items()]}, allow_null=True)


        # DISPLAY EXPRESSION
        ess_layer_name = self.essences.name()
        display_expression = f"""
            WITH_VARIABLE(
                'ess',
                get_feature(
                    '{ess_layer_name}',
                    'fid',
                    coalesce(NULLIF("REG_ESSENCE_ID", ''), "REG_ESSENCE_SECONDAIRE_ID")
                ),
                concat(
                    attribute(@ess, 'essence_variation'),
                    ' : ',
                    "REG_STADE",
                    ' - '
                    "REG_ETAT"
                )
            )
            """
        self.layer.setDisplayExpression(display_expression)

    def _configure_essence(self):

        configure_essence_field(
            self.layer,
            "REG_ESSENCE_ID",
            "REG_ESSENCE_SECONDAIRE_ID",
            self.essences,
            self.codes,
            with_variation=False
        )

    def _set_qfield_properties(self):
        self.layer.setCustomProperty(
            "QFieldSync/value_map_button_interface_threshold",
            len(self.codes) + 1
        )