from qgis.core import QgsFieldConstraints

from ....core.layer.manager import FormBuilder, FieldEditor

class RegConfigurator:

    def __init__(self, layer, essences):

        self.layer = layer
        self.essences = essences

        self.fb = FormBuilder(layer)
        self.fe = FieldEditor(layer)

    def configure(self):

        print("configure REG layer")
        self._init_form()
        self._configure_fields()
        self._set_qfield_properties()
      
    def _init_form(self):
        self.fb.init_form()
        self.fb.new_add_fields(["REG_ESS", "REG_STADE", "REG_ETAT"])
        self.fb.apply()

    def _configure_fields(self):
               # ALIASES
        aliases = [
            ("REG_ESS", "Essence"),
            ("REG_STADE", "Stade"),
            ("REG_ETAT", "Etat"),
        ]
        
        for field, alias in aliases:
            self.fe.set_alias(field, alias)

        # DISPLAY EXPRESSION
        ess_layer_name = self.essences.name()
        display_expression = f"""
            WITH_VARIABLE(
                'ess',
                get_feature('{ess_layer_name}', 'fid', "REG_ESS"),
                concat(attribute(@ess, 'essence_variation'), ' : ', "REG_STADE", ' - ', "REG_ETAT")
            )
            """
        self.layer.setDisplayExpression(display_expression)

        # REG_ESS
        field_name = "REG_ESS"
        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        config = {
            'FilterExpression': '"variation" IS NULL',
            'Key': 'fid',
            'LayerName': self.essences.name(),
            'Value': 'essence_variation'
        }
        self.fe.add_value_relation(field_name, config)

        # REG_STADE
        self.stades = {
            "semis_inf_05": "Semis <0.5m",
            "semis_05_1": "Semis 0.5-1m",
            "fourre_1_3": "Fourré 1-3m",
            "semis_3_5": "Gaulis 3-5m",
            "semis_5_15": "Perchis 5m-15cm"
        }
        self.fe.add_value_map('REG_STADE', {'map': [{str(value): str(descr)} for descr, value in self.stades.items()]})

        # REG_ETAT
        self.etats = {
            "continue_sup_80": "Continue >80%",
            "conseqente_50_80": "Conséquente 50-80%",
            "moderee_30_50": "Modérée 30-50%",
            "eparse_10_30": "Eparse 10-30%",
            "infime_inf_10": "Infime <10%"
        }
        self.fe.add_value_map('REG_ETAT', {'map': [{str(value): str(descr)} for descr, value in self.etats.items()]})

    def _set_qfield_properties(self):
        
        treshold = min(len(self.stades) + 1, len(self.etats) +1)
        
        self.layer.setCustomProperty("QFieldSync/value_map_button_interface_threshold", treshold)