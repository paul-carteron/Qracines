from PyQt5.QtGui import QColor, QFont
from qgis.core import (
    Qgis,
    QgsFieldConstraints,
    QgsMarkerSymbol,
    QgsPalLayerSettings,
    QgsSingleSymbolRenderer,
    QgsTextBufferSettings,
    QgsTextFormat,
    QgsVectorLayerSimpleLabeling,
)

from ....core.layer import FieldEditor, FormBuilder
from ..config import (
    EXPOSURE_CHOICES,
    HUMUS_CHOICES,
    STOP_CHOICES,
    TOPOGRAPHY_CHOICES,
)


class SondageConfigurator:
    def __init__(self, layer, stations, relation=None, guide=None):
        self.layer = layer
        self.stations = stations
        self.relation = relation
        self.guide = guide
        self.fields = FieldEditor(layer)
        self.form = FormBuilder(layer)

    def configure(self):
        self._init_form()
        self._configure_fields()
        self._set_qfield_properties()
        self._style()

    def _init_form(self):
        self.form.init_form()
        self.form.add_fields(["HUMUS", "TOPOGRAPHIE", "EXPOSITION", "STATION"])
        self.form.add_relation(self.relation, alias="Profil pédologique",)
        self.form.add_fields(["ARRET", "REMARQUE", "PHOTO"])
        self.form.apply()

    def _configure_fields(self):

        # region GUIDE
        self.fields.set_alias("GUIDE", "Guide de station")
        if self.guide:
            escaped_guide = self.guide.replace("'", "''")
            self.fields.set_default_value("GUIDE", f"'{escaped_guide}'")
            self.fields.set_constraint(
                "GUIDE", QgsFieldConstraints.ConstraintNotNull
            )
            self.fields.set_read_only("GUIDE")
        # endregion

        # region UUID
        self.fields.set_default_value("UUID", "uuid()")
        self.fields.set_constraint(
            "UUID", QgsFieldConstraints.ConstraintNotNull
        )
        self.fields.set_constraint(
            "UUID", QgsFieldConstraints.ConstraintUnique
        )
        self.fields.set_read_only("UUID")
        # endregion

        # region REMARQUE
        self.fields.set_alias("REMARQUE", "Remarques")
        # endregion

        # region HUMUS
        self.fields.set_alias("HUMUS", "Humus")
        self.fields.add_value_map(
            "HUMUS", {"map": [{choice: choice} for choice in HUMUS_CHOICES]}
        )
        # endregion

        # region TOPOGRAPHIE
        self.fields.set_alias("TOPOGRAPHIE", "Topographie")
        self.fields.add_value_map(
            "TOPOGRAPHIE",
            {"map": [{label: value} for label, value in TOPOGRAPHY_CHOICES.items()]},
        )
        # endregion

        # region EXPOSITION
        self.fields.set_alias("EXPOSITION", "Exposition")
        self.fields.add_value_map(
            "EXPOSITION",
            {"map": [{label: value} for label, value in EXPOSURE_CHOICES.items()]},
        )
        # endregion

        # region STATION
        self.fields.set_alias("STATION", "Station")
        self.fields.add_value_map(
            "STATION",
            {"map": [{str(station): str(station)} for station in self.stations]},
        )
        # endregion

        # region ARRET
        self.fields.set_alias("ARRET", "Cause d'arrêt")
        self.fields.add_value_map(
            "ARRET", {"map": [{choice: choice} for choice in STOP_CHOICES]}
        )
        # endregion

        # region PHOTO
        self.fields.add_external_resource("PHOTO")
        # endregion

    def _set_qfield_properties(self):
        self.layer.setCustomProperty(
            "QFieldSync/value_map_button_interface_threshold", 5
        )

    def _style(self):
        symbol = QgsMarkerSymbol.createSimple(
            {
                "name": "cross2",
                "color": "227,26,28,255",
                "outline_color": "227,26,28,255",
                "outline_width": "0.6",
                "size": "2.5",
            }
        )
        self.layer.setRenderer(QgsSingleSymbolRenderer(symbol))

        label_settings = QgsPalLayerSettings()
        label_settings.fieldName = "fid"
        label_settings.placement = Qgis.LabelPlacement.OverPoint

        text_format = QgsTextFormat()
        text_format.setFont(QFont("Arial", 10))
        text_format.setSize(10)
        text_format.setColor(QColor(191, 22, 24))

        buffer = QgsTextBufferSettings()
        buffer.setEnabled(True)
        buffer.setSize(1)
        buffer.setColor(QColor(250, 250, 250))
        text_format.setBuffer(buffer)

        label_settings.setFormat(text_format)
        self.layer.setLabeling(QgsVectorLayerSimpleLabeling(label_settings))
        self.layer.setLabelsEnabled(True)
        self.layer.triggerRepaint()
