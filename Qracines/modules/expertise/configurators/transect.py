from qgis.core import QgsFieldConstraints

from ....core.layer import FormBuilder, FieldEditor
from ....utils.essence import configure_essence_field

class TransectConfigurator:

    def __init__(self, layer, dendro, essences, lst_hauteur, lst_diam):

        self.layer = layer
        self.dendro = dendro
        self.essences = essences
        self.lst_hauteur = lst_hauteur
        self.lst_diam = lst_diam

        self.fb = FormBuilder(layer)
        self.fe = FieldEditor(layer)

    def configure(self):

        print("configure TRANSECT layer")

        self._init_form()
        self._configure_fields()
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

        # region TR_DIAMETRE
        field_name = "TR_DIAMETRE"
        config = {
            'Key': 'VALEUR',
            'Layer': self.lst_diam.id(),
            'Value': 'VALEUR',
            'AllowNull': False,
            'FilterExpression': '''
            "VALEUR" >= attribute(get_feature_by_id('param',1), 'DMIN') 
            AND 
            "VALEUR" <= attribute(get_feature_by_id('param',1), 'DMAX')
            '''
        }

        self.fe.add_value_relation(field_name, config)

        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        self.fe.set_constraint_expression(field_name,
            f'"{field_name}" != \'\'',
            f"Le champ {field_name} ne peut pas être vide.", 
            QgsFieldConstraints.ConstraintStrengthHard
        )
        # endregion

        # region TR_HAUTEUR
        field_name = "TR_HAUTEUR"
        config = {
            'Key': 'VALEUR',
            'Layer': self.lst_hauteur.id(),
            'Value': 'VALEUR',
            'AllowNull': False,
            'FilterExpression': '''
            "VALEUR" >= attribute(get_feature_by_id('param',1), 'HMIN') 
            AND 
            "VALEUR" <= attribute(get_feature_by_id('param',1), 'HMAX')
            '''
        }
        self.fe.add_value_relation(field_name, config)

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

        # region TR_ESSENCE_ID - TR_ESSENCE_SECONDAIRE_ID
        field_ess = "TR_ESSENCE_ID"
        field_ess2 = "TR_ESSENCE_SECONDAIRE_ID"
        config = {
            'Key': 'fid',
            'Layer': self.essences.id(),
            'Value': 'essence_variation',
            'AllowNull': True,
            'FilterExpression': '"selected" = true'
        }

        self.fe.add_value_relation(field_ess, config)

        config = {
            'Key': 'fid',
            'Layer': self.essences.id(),
            'Value': 'essence_variation',
            'AllowNull': True,
            'FilterExpression': '"selected" = false OR "selected" IS NULL'
        }

        self.fe.add_value_relation(field_ess2, config)

        expr = f'''(COALESCE("{field_ess}", '') <> '') != (COALESCE("{field_ess2}", '') <> '')'''
        msg = "Veuillez sélectionner une valeur pour ESSENCE ou ESSENCE_SECONDAIRE (mais pas les deux)."
        self.fe.set_constraint_expression(field_ess, expr, msg, QgsFieldConstraints.ConstraintStrengthHard)
        # endregion

    def _set_qfield_properties(self):

        threshold = 70

        self.layer.setCustomProperty(
            "QFieldSync/value_map_button_interface_threshold",
            threshold
        )