from ....core.layer import FormBuilder, FieldEditor

class EssencesConfigurator:

    def __init__(self, layer):
        self.layer = layer

        self.fb = FormBuilder(layer)
        self.fe = FieldEditor(layer)

    def configure(self):
        
        self._init_form()
        self._configure_fields()

    def _init_form(self):
        
        self.fb.init_form()
        self.fb.new_add_fields(["selected"])
        self.fb.apply()

    def _configure_fields(self):
        
        self.fe.set_alias("selected", "SELECTION ESSENCE")