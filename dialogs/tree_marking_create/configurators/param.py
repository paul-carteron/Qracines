
from qgis.core import QgsFieldConstraints

from ....core.layer.manager import FormBuilder, FieldEditor

from ...tree_marking_config import TYPE_CHOICES, MARQUAGE_CHOICES, COULEUR_CHOICES, MARTEAU_CHOICES

class ParamConfigurator:

    def __init__(self, layer):
        self.layer = layer
        self.fb = FormBuilder(layer)
        self.fe = FieldEditor(layer)

    def configure(self):
        
        self._init_form()
        self._configure_fields()

    def _init_form(self):

        self.fb.init_form() 
        self.fb.new_add_fields(["TYPE", "LOT", "PARCELLE", "SURFACE", "MARQUE","MARQUAGE_BO", "COULEUR_BO", "MARQUAGE_BI", "COULEUR_BI"])
        self.fb.apply()

    def _configure_fields(self):

        aliases = [
            ("TYPE", "Type"),
            ("LOT", "Lot"),
            ("PARCELLE", "Parcelle"),
            ("SURFACE", "Surface [ha]"),
            ("MARQUAGE_BO", "Marquage BO"),
            ("COULEUR_BO", "Couleur BO"),
            ("MARQUAGE_BI", "Marquage BI"),
            ("COULEUR_BI", "Couleur BI"),
            ("MARQUE", "Marque"),
        ]
        
        for field, alias in aliases:
            self.fe.set_alias(field, alias)

        reuse = ["TYPE", "LOT","MARQUAGE_BO", "COULEUR_BO", "MARQUAGE_BI", "COULEUR_BI"]
        for field_name in reuse:
            self.fe.set_reuse_last_value(field_name)

        self.fe.set_constraint("TYPE", QgsFieldConstraints.ConstraintNotNull)
        self.fe.set_constraint("LOT", QgsFieldConstraints.ConstraintNotNull)
        self.fe.set_constraint("PARCELLE", QgsFieldConstraints.ConstraintNotNull)

        self.fe.set_constraint("SURFACE", QgsFieldConstraints.ConstraintNotNull)
        self.fe.add_range("SURFACE", {'AllowNull': False, 'Max': 1000, 'Min': 0, 'Precision': 2, 'Step': 0.01})
        self.fe.set_constraint_expression("SURFACE", f' SURFACE > 0', "La surface doit être supérieur à 0", strength=QgsFieldConstraints.ConstraintStrengthHard)

        self.fe.add_value_map("TYPE", {'map': [{v: k} for k, v in TYPE_CHOICES.items()]})

        for field_name in ["MARQUAGE_BO", "MARQUAGE_BI"]:
            self.fe.add_value_map(field_name, {'map': [{v: k} for k, v in MARQUAGE_CHOICES.items()]})

        for field_name in ["COULEUR_BO", "COULEUR_BI"]:
            self.fe.add_value_map(field_name, {'map': [{v: k} for k, v in COULEUR_CHOICES.items()]})

        self.fe.add_value_map("MARQUE", {'map': [{v: k} for k, v in MARTEAU_CHOICES.items()]})
