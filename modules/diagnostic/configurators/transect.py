from qgis.core import QgsFieldConstraints

from .....core.layer.manager import FormBuilder, FieldEditor

class TransectConfigurator:

    def __init__(self, layer, dendro, essences):

        self.layer = layer
        self.dendro = dendro
        self.essences = essences

        self.fb = FormBuilder(layer)
        self.fe = FieldEditor(layer)

    def configure(self):

        print("configure TRANSECT layer")
        self._init_form()
        self._configure_fields()
        self._style()
        self._set_qfield_properties()

    def _init_form(self):
        
        self.fb.init_form()

        self.fb.new_add_fields(["TR_PARCELLE"])
        grp_essence = self.fb.create_group(name="Essence")
        self.fb.new_add_fields(["TR_TYPE_ESS", "TR_ESS"], grp_essence)

        grp_dendro = self.fb.create_group(name="Dendrométrie", columns=2)
        self.fb.new_add_fields(["TR_DIAM", "TR_HAUTEUR"], grp_dendro)

        self.fb.new_add_fields(["TR_EFFECTIF"])
        
        self.fb.apply()

    def _configure_fields(self):
        # ALIASES
        aliases = [
            ("TR_PARCELLE", "PRF/SPRF"),
            ("TR_TYPE_ESS", "Type Essence"),
            ("TR_ESS", "Essence Transect"),
            ("TR_DIAM", "Diamètre (cm)"),
            ("TR_HAUTEUR", "Hauteur (m)"),
            ("TR_EFFECTIF", "Effectif"),]
        
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

        # TR_PARCELLE
        field_name = "TR_PARCELLE"
        self.fe.set_reuse_last_value(field_name)
        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)

        # TR_TYPE_ESS
        field_name = "TR_TYPE_ESS"
        types = {f["type"]: f["type"] for f in self.essences.getFeatures()}
        self.fe.add_value_map(field_name, {'map': [{str(name): str(code)} for code, name in types.items()]})
        self.fe.set_reuse_last_value(field_name)

        # TR_ESS
        field_name = "TR_ESS"
        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        config = {
            'FilterExpression': f"\"type\" = current_value('TR_TYPE_ESS')",
            'Key': 'fid',
            'LayerName': self.essences.name(),
            'Value': 'essence_variation'
        }
        self.fe.add_value_relation(field_name, config)
        self.fe.set_reuse_last_value(field_name)

        # TR_DIAM
        field_name = "TR_DIAM"
        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        dmin, dmax = self.dendro['dmin'], self.dendro['dmax']
        self.fe.add_value_map(field_name, {'map': [{str(d): str(d)} for d in range(dmin, dmax + 1, 5)]})
        expression = '"TR_DIAM" != \'\''
        description = "Le champ TR_DIAM ne peut pas être vide."
        self.fe.set_constraint_expression(field_name, expression, description, QgsFieldConstraints.ConstraintStrengthHard)

        # TR_HAUTEUR
        field_name = "TR_HAUTEUR"
        hmin, hmax = self.dendro['hmin'], self.dendro['hmax']
        self.fe.add_value_map(field_name, {'map': [{str(h): str(h)} for h in range(hmin, hmax + 1)]})

        # TR_EFFECTIF
        field_name = "TR_EFFECTIF"
        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        self.fe.add_range(field_name, {'AllowNull': False, 'Max': 1000, 'Min': 0, 'Precision': 0, 'Step': 1})
        self.fe.set_default_value(field_name, '1', False)

    def _style(self):
        s = self.layer.renderer().symbol()
        s.symbolLayer(0).setSize(2)
        self.layer.triggerRepaint()

    def _set_qfield_properties(self):

        threshold = max(
            self.dendro["hmax"] + 1,
            (self.dendro["dmax"] + 1) / 5
        )

        self.layer.setCustomProperty(
            "QFieldSync/value_map_button_interface_threshold",
            threshold
        )
