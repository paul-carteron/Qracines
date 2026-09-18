from qgis.core import QgsAttributeEditorQmlElement, QgsFieldConstraints

from ....core.layer import FieldEditor, FormBuilder
from ..config import (
    CARBONATION_LOCATION_CHOICES,
    CARBONATION_POWER_CHOICES,
    COARSE_FRAGMENT_SIZE_CHOICES,
    COMPACTNESS_CHOICES,
    HYDROMORPHY_CHOICES,
    PROPORTION_CHOICES,
    SOIL_MOISTURE_CHOICES,
    STRUCTURE_CHOICES,
    TEXTURE_CHOICES,
    THICKNESS_CHOICES,
)


class HorizonsConfigurator:
    def __init__(self, layer):
        self.layer = layer
        self.fields = FieldEditor(layer)
        self.form = FormBuilder(layer)

    def configure(self):
        self._init_form()
        self._configure_fields()
        self._set_qfield_properties()

    def _init_form(self):
        self.form.init_form()
        self.form.add_fields(["TYPE", "EPAISSEUR"])

        texture_image = QgsAttributeEditorQmlElement("Triangle des textures", self.form.root)
        texture_image.setShowLabel(False)
        texture_image.setQmlCode(
            r'''import QtQuick

                Image {
                    width: parent.width
                    height: sourceSize.width > 0
                        ? width * sourceSize.height / sourceSize.width
                        : 0
                    source: "file:///" + expression.evaluate(
                        "replace(@project_folder, '\\\\', '/') || '/assets/triangle_des_textures.jpeg'"
                    )
                    fillMode: Image.PreserveAspectFit
                }'''
        )
        self.form.root.addChildElement(texture_image)

        self.form.add_fields(["TEXTURE", "HUMIDITE", "COULEUR"])
        structure_group = self.form.add_group(
            "", columns=1, visibility_expression='"TYPE" = \'Fosse\''
        )
        self.form.add_fields(["STRUCTURE"], structure_group)

        self.form.add_fields(["COMPACITE", "EG"])
        eg_group = self.form.add_group(
            "", columns=2, visibility_expression='"EG" = TRUE'
        )
        self.form.add_fields(["EG_TAILLE", "EG_PROPORTION"], eg_group)

        self.form.add_fields(["HM"])
        hm_group = self.form.add_group(
            "", columns=2, visibility_expression='"HM" = TRUE'
        )
        self.form.add_fields(["HM_TACHE", "HM_PROPORTION"], hm_group)

        self.form.add_fields(["CAR"])
        car_group = self.form.add_group(
            "", columns=2, visibility_expression='"CAR" = TRUE'
        )
        self.form.add_fields(
            ["CAR_LOCALISATION", "CAR_PUISSANCE"], car_group
        )
        self.form.apply()

    def _configure_fields(self):
        # region SONDAGE
        self.fields.set_alias("SONDAGE", "Sondage")
        # endregion

        # region TYPE
        self.fields.set_alias("TYPE", "Type sondage")
        self.fields.set_default_value("TYPE", "'Tarriere'")
        self.fields.set_constraint(
            "TYPE",
            QgsFieldConstraints.ConstraintNotNull,
            QgsFieldConstraints.ConstraintStrengthSoft,
        )
        self.fields.add_checkbox(
            "TYPE",
            {
                "AllowNullState": False,
                "CheckedState": "Tarriere",
                "TextDisplayMethod": 1,
                "UncheckedState": "Fosse",
            },
        )
        # endregion

        # region EPAISSEUR
        self.fields.set_alias("EPAISSEUR", "Epaisseur")
        self.fields.set_constraint(
            "EPAISSEUR",
            QgsFieldConstraints.ConstraintNotNull,
            QgsFieldConstraints.ConstraintStrengthSoft,
        )
        self.fields.add_value_map(
            "EPAISSEUR",
            {"map": [{str(value): str(value)} for value in THICKNESS_CHOICES]},
        )
        # endregion

        # region HUMIDITE
        self.fields.set_alias("HUMIDITE", "Humidité")
        self.fields.add_value_map(
            "HUMIDITE",
            {
                "map": [
                    {label: value}
                    for label, value in SOIL_MOISTURE_CHOICES.items()
                ]
            },
        )
        # endregion

        # region TEXTURE
        self.fields.set_alias("TEXTURE", "Texture")
        self.fields.set_constraint(
            "TEXTURE",
            QgsFieldConstraints.ConstraintNotNull,
            QgsFieldConstraints.ConstraintStrengthSoft,
        )
        self.fields.add_value_map(
            "TEXTURE",
            {"map": [{value: value} for value in TEXTURE_CHOICES]},
        )
        # endregion

        # region COULEUR
        self.fields.set_alias("COULEUR", "Couleur")
        # endregion

        # region STRUCTURE
        self.fields.set_alias("STRUCTURE", "Structure")
        self.fields.add_value_map(
            "STRUCTURE",
            {
                "map": [
                    {label: value}
                    for label, value in STRUCTURE_CHOICES.items()
                ]
            },
        )
        # endregion

        # region COMPACITE
        self.fields.set_alias("COMPACITE", "Compacité")
        self.fields.add_value_map(
            "COMPACITE",
            {
                "map": [
                    {label: value}
                    for label, value in COMPACTNESS_CHOICES.items()
                ]
            },
        )
        # endregion

        # region EG
        self.fields.set_alias("EG", "Eléments grossiers ?")
        self.fields.add_checkbox(
            "EG", {"AllowNullState": False, "TextDisplayMethod": 0}
        )
        # endregion

        # region EG_TAILLE
        self.fields.set_alias("EG_TAILLE", "Eléments grossiers")
        self.fields.add_value_map(
            "EG_TAILLE",
            {
                "map": [
                    {label: value}
                    for label, value in COARSE_FRAGMENT_SIZE_CHOICES.items()
                ]
            },
        )
        # endregion

        # region EG_PROPORTION
        self.fields.set_alias("EG_PROPORTION", "% d'éléments grossiers")
        self.fields.add_value_map(
            "EG_PROPORTION",
            {"map": [{str(value): str(value)} for value in PROPORTION_CHOICES]},
        )
        # endregion

        # region HM
        self.fields.set_alias("HM", "Hydromorphie ?")
        self.fields.add_checkbox(
            "HM", {"AllowNullState": False, "TextDisplayMethod": 0}
        )
        # endregion

        # region HM_TACHE
        self.fields.set_alias("HM_TACHE", "Hydromorphie")
        self.fields.add_value_map(
            "HM_TACHE",
            {
                "map": [
                    {label: value}
                    for label, value in HYDROMORPHY_CHOICES.items()
                ]
            },
        )
        # endregion

        # region HM_PROPORTION
        self.fields.set_alias("HM_PROPORTION", "% d'hydromorphie")
        self.fields.add_value_map(
            "HM_PROPORTION",
            {"map": [{str(value): str(value)} for value in PROPORTION_CHOICES]},
        )
        # endregion

        # region CAR
        self.fields.set_alias("CAR", "Carbonatation ?")
        self.fields.add_checkbox(
            "CAR", {"AllowNullState": False, "TextDisplayMethod": 0}
        )
        # endregion

        # region CAR_LOCALISATION
        self.fields.set_alias("CAR_LOCALISATION", "Carbonatation")
        self.fields.add_value_map(
            "CAR_LOCALISATION",
            {
                "map": [
                    {label: value}
                    for label, value in CARBONATION_LOCATION_CHOICES.items()
                ]
            },
        )
        # endregion

        # region CAR_PUISSANCE
        self.fields.set_alias(
            "CAR_PUISSANCE", "Puissance de la carbonatation"
        )
        self.fields.add_value_map(
            "CAR_PUISSANCE",
            {
                "map": [
                    {label: value}
                    for label, value in CARBONATION_POWER_CHOICES.items()
                ]
            },
        )
        # endregion

        # DISPLAY EXPRESSION
        display_expression = f"""
            COALESCE("TEXTURE", '') || ' — ' || COALESCE(to_string("EPAISSEUR"), '') || ' cm'
        """
        self.layer.setDisplayExpression(display_expression)

    def _set_qfield_properties(self):
        self.layer.setCustomProperty(
            "QFieldSync/value_map_button_interface_threshold", 5
        )
