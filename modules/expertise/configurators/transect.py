from qgis.core import QgsFieldConstraints

from .....core.layer.manager import FormBuilder, FieldEditor
from .....utils.essence import configure_essence_field

class TransectConfigurator:

    def __init__(self, layer, dendro, essences, codes):

        self.layer = layer
        self.dendro = dendro
        self.essences = essences
        self.codes = codes

        self.fb = FormBuilder(layer)
        self.fe = FieldEditor(layer)

    def configure(self):

        print("configure TRANSECT layer")

        self._init_form()
        self._configure_fields()
        self._configure_essence()
        self._set_qfield_properties()

    def _init_form(self):

        self.fb.init_form()

        self.fb.new_add_fields([
            "TR_PARCELLE",
            "TR_STRATE",
            "TR_ESSENCE_ID",
            "TR_ESSENCE_SECONDAIRE_ID",
            "TR_DIAMETRE",
            "TR_EFFECTIF",
            "TR_HAUTEUR"
        ])

        self.fb.apply()

    def _configure_fields(self):

        aliases = {
            "TR_PARCELLE": "Parcelle",
            "TR_STRATE": "Strate",
            "TR_ESSENCE_ID": "Essence",
            "TR_ESSENCE_SECONDAIRE_ID": "Autre essence",
            "TR_DIAMETRE": "Diamètre [cm]",
            "TR_EFFECTIF": "Effectif",
            "TR_HAUTEUR": "Hauteur [m]",
        }

        for field, alias in aliases.items():
            self.fe.set_alias(field, alias)

        # UUID
        field = "UUID"
        self.fe.set_constraint(field, QgsFieldConstraints.ConstraintUnique)
        self.fe.set_constraint(field, QgsFieldConstraints.ConstraintNotNull)
        self.fe.set_default_value(field, "uuid()", apply_on_update=False)

        # TR_PARCELLE & TR_STRATE
        expr = '"TR_PARCELLE" is not NULL OR "TR_STRATE" is not NULL'
        msg = "Ajouter une parcelle ou une strate si l'inventaire n'utilise pas de carto"
        
        self.fe.set_constraint_expression("TR_PARCELLE", expr, msg)
        self.fe.set_constraint_expression("TR_STRATE", expr, msg)

        self.fe.set_reuse_last_value("TR_PARCELLE")
        self.fe.set_reuse_last_value("TR_STRATE")

        # TR_DIAMETRE
        field = "TR_DIAMETRE"
        dmin = self.dendro["dmin"]
        dmax = self.dendro["dmax"]

        self.fe.set_constraint(field, QgsFieldConstraints.ConstraintNotNull)
        self.fe.add_value_map(field,{"map": [{str(d): str(d)} for d in range(dmin, dmax + 1, 5)]})

        expr = '"TR_DIAMETRE" != \'\''
        msg = "Le champ TR_DIAMETRE ne peut pas être vide."

        self.fe.set_constraint_expression(field,expr,msg,QgsFieldConstraints.ConstraintStrengthHard)

        # TR_EFFECTIF
        field = "TR_EFFECTIF"
        self.fe.set_constraint(field, QgsFieldConstraints.ConstraintNotNull)
        self.fe.add_range(
            field,
            {
                "AllowNull": False,
                "Max": 1000,
                "Min": 0,
                "Precision": 0,
                "Step": 1,
            }
        )

        self.fe.set_default_value(field, "1", False)

        # TR_HAUTEUR
        field = "TR_HAUTEUR"
        hmin = self.dendro["hmin"]
        hmax = self.dendro["hmax"]

        self.fe.add_value_map(field, {"map": [{str(h): str(h)} for h in range(hmin, hmax + 1)]})

    def _configure_essence(self):

        configure_essence_field(
            self.layer,
            "TR_ESSENCE_ID",
            "TR_ESSENCE_SECONDAIRE_ID",
            self.essences,
            self.codes,
            with_variation=True
        )

    def _set_qfield_properties(self):

        threshold = max(
            self.dendro["hmax"] + 1,
            (self.dendro["dmax"] + 1) / 5
        )

        self.layer.setCustomProperty(
            "QFieldSync/value_map_button_interface_threshold",
            threshold
        )