
from qgis.core import QgsFieldConstraints

from ....core.layer import FormBuilder, FieldEditor

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
        self.fb.new_add_fields(["HMIN", "HMAX", "DMIN", "DMAX"])
        self.fb.apply()

    def _configure_fields(self):

        aliases = [
            ("HMIN", "Hauteur minimale [m]"),
            ("HMAX", "Hauteur maximale [m]"),
            ("DMIN", "Diamètre minimal [cm]"),
            ("DMAX", "Diamètre maximal [cm]"),
        ]

        for field, alias in aliases:
            self.fe.set_alias(field, alias)

        h_config = {'AllowNull': False, 'Max': 40, 'Min': 1, 'Precision': 0, 'Step': 1, 'Style': 'Slider'}
        d_config = {'AllowNull': False, 'Max': 200, 'Min': 5, 'Precision': 0, 'Step': 5, 'Style': 'Slider'}

        self.fe.add_range("HMIN", h_config)
        self.fe.set_default_value("HMIN", "3")
                
        self.fe.add_range("HMAX", h_config)
        self.fe.set_default_value("HMAX", "15")

        self.fe.add_range("DMIN", d_config)
        self.fe.set_default_value("DMIN", "30")

        self.fe.add_range("DMAX", d_config)
        self.fe.set_default_value("DMAX", "100")
