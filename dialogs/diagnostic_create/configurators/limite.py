from qgis.PyQt.QtCore import Qt
from qgis.core import (
    QgsRendererCategory,
    QgsCategorizedSymbolRenderer,
    QgsSymbol,
    QgsSimpleLineSymbolLayer
)

from PyQt5.QtGui import QColor

from ....core.layer.manager import FormBuilder, FieldEditor
from ....utils.config import get_limites, get_limites_config


class LimiteConfigurator:

    def __init__(self, layer):
        self.layer = layer
        self.fb = FormBuilder(layer)
        self.fe = FieldEditor(layer)

    def configure(self):
        print("configure LIMITE layer")
        self._init_form()
        self._configure_fields()
        self._style()

    def _init_form(self):
        self.fb.init_form()
        self.fb.new_add_fields(["LIMITE_TYPE", "LIMITE_RMQ", "LIMITE_PHOTO"])
        self.fb.apply()

    def _configure_fields(self):

        # ALIASES
        aliases = [
            ("LIMITE_TYPE", "Type"),
            ("LIMITE_RMQ", "Remarque"),
            ("LIMITE_PHOTO", "Photo"),
        ]
        
        for field, alias in aliases:
            self.fe.set_alias(field, alias)

        # LIMITE_TYPE
        limites = get_limites()
        self.fe.add_value_map('LIMITE_TYPE', {'map': [{str(name): str(code)} for code, name in limites.items()]})

        # LIMITE_PHOTO
        self.fe.add_external_resource("LIMITE_PHOTO")

    def _style(self):

        field = "LIMITE_TYPE"
        cfg = get_limites_config()

        style_map = {
            "solid": Qt.SolidLine,
            "dash": Qt.DashLine,
            "dot": Qt.DotLine,
            "dashdot": Qt.DashDotLine,
            "dashdotdot": Qt.DashDotDotLine,
        }

        categories = []

        for code, props in cfg.items():

            color = QColor(props.get("color", "black"))
            width = float(props.get("width", 0.6))
            line_type = props.get("style", "solid").lower()
            label = props.get("label", code)

            line_layer = QgsSimpleLineSymbolLayer()
            line_layer.setColor(color)
            line_layer.setWidth(width)
            line_layer.setPenStyle(style_map.get(line_type, Qt.SolidLine))

            symbol = QgsSymbol.defaultSymbol(self.layer.geometryType())
            symbol.deleteSymbolLayer(0)
            symbol.appendSymbolLayer(line_layer)

            categories.append(QgsRendererCategory(code, symbol, label))

        renderer = QgsCategorizedSymbolRenderer(field, categories)

        self.layer.setRenderer(renderer)
        self.layer.triggerRepaint()