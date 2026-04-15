from qgis.core import QgsFieldConstraints
from ....core.layer import FormBuilder, FieldEditor
from ....utils.config import get_peuplements

class PlacetteConfigurator:

    def __init__(self, layer, relations):
        self.layer = layer
        self.relations = relations
        self.fb = FormBuilder(layer)
        self.fe = FieldEditor(layer)

    def configure(self):
        print("configure PLACETTE layer")
        self._init_form()
        self._configure_fields()
        self._set_qfield_properties()

    def _init_form(self):

        self.fb.init_form()

        general_tab = self.fb.create_tab("Général")

        self.fb.new_add_fields(
            ["COMPTEUR", "PLTM_PARCELLE", "PLTM_STRATE", "PLTM_TYPE", "PLA_RMQ"],
            parent=general_tab
        )

        self.fb.new_add_relation(self.relations["gha"], parent=general_tab)

        self.fb.new_add_fields(["TSE_STERE_HA"], parent=general_tab)

        self.fb.new_add_relation(self.relations["tse"], parent=general_tab)
        self.fb.new_add_relation(self.relations["va"], parent=general_tab)
        self.fb.new_add_relation(self.relations["reg"], parent=general_tab)

        self.fb.apply()

    def _configure_fields(self):
        # ALIASES
        aliases = [
            ("COMPTEUR", "Placette"),
            ("PLTM_PARCELLE", "Parcelle"),
            ("PLTM_STRATE", "Strate"),
            ("PLA_RMQ", "Remarque"),
            ("PLTM_TYPE", "Type de peuplement"),
            ("TSE_STERE_HA", "Taillis [st/ha]")]
        
        for field, alias in aliases:
            self.fe.set_alias(field, alias)

        # UUID
        # If apply_on_update=True, uuid() resets on each children edit: 
        # - Create parent → UUID=A 
        # - Add first child → FK=A 
        # - Edit another child → UUID becomes B (child’s FK=A breaks under Composition) 
        # - Add second child → FK=B 
        # Only the last child stays linked. Using apply_on_update=False keeps the UUID stable so all children link correctly.
        field_name = "UUID"
        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintUnique)
        self.fe.set_default_value(field_name, "uuid()", apply_on_update=False)
        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)

        # COMPTEUR
        field_name = "COMPTEUR"
        self.fe.set_read_only(field_name)
        self.fe.set_default_value(field_name, 'count("fid") + 1')

        # PLTM_PARCELLE & PLTM_STRATE
        expression = '"PLTM_PARCELLE" is not NULL OR "PLTM_STRATE" is not NULL'
        description = "Ajouter une parcelle ou une strate si l'inventaire n'utilise pas de carto"
        self.fe.set_constraint_expression("PLTM_PARCELLE", expression, description)
        self.fe.set_constraint_expression("PLTM_STRATE", expression, description)
        self.fe.set_reuse_last_value ("PLTM_PARCELLE")
        self.fe.set_reuse_last_value("PLTM_STRATE")

        # PLTM_TYPE
        peuplements = get_peuplements()
        self.fe.add_value_map('PLTM_TYPE', {'map': [{str(name): str(code)} for code, name in peuplements.items()]}, allow_null=True)

        # TSE_STERE_HA
        stere_ha = [*range(0, 200, 25), *range(200, 400, 50)]
        self.fe.add_value_map("TSE_STERE_HA", {'map': [{str(value): str(value)} for value in stere_ha]})

    def _set_qfield_properties(self):

        threshold = len(get_peuplements())

        self.layer.setCustomProperty(
            "QFieldSync/value_map_button_interface_threshold",
            threshold
        )