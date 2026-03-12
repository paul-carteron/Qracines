
from qgis.core import (
    QgsSimpleMarkerSymbolLayer,
    QgsSymbolLayer,
    QgsProperty,
    QgsSingleSymbolRenderer,
    QgsSymbol
)

from ....core.layer import FormBuilder, FieldEditor
from ....utils.config import get_pictos

class PictoConfigurator:

    def __init__(self, layer):
        self.layer = layer
        self.fb = FormBuilder(layer)
        self.fe = FieldEditor(layer)

    def configure(self):
        print("configure PICTO layer")
        self._init_form()
        self._configure_fields()
        self._style()

    def _init_form(self):
        self.fb.init_form()
        self.fb.new_add_fields(["PICTO_TYPE", "PICTO_RMQ", "PICTO_PHOTO"])
        grp_shape = self.fb.create_group(name="Symbologie", columns=2)
        self.fb.new_add_fields(["PICTO_COLOR", "PICTO_SHAPE"], grp_shape)
        self.fb.apply()

    def _configure_fields(self):
        # ALIASES
        aliases = [
            ("PICTO_TYPE", "Type"),
            ("PICTO_RMQ", "Remarque"),
            ("PICTO_PHOTO", "Photo"),
            ("PICTO_COLOR", "Couleur"),
            ("PICTO_SHAPE", "Forme"),
        ]
        
        for field, alias in aliases:
            self.fe.set_alias(field, alias)

        # PICTO_TYPE
        pictos = get_pictos()
        self.fe.add_value_map('PICTO_TYPE', {'map': [{str(name): str(code)} for code, name in pictos.items()]})

        # PICTO_PHOTO
        self.fe.add_external_resource("PICTO_PHOTO")

        # PICTO_COLOR
        self.fe.add_color_picker("PICTO_COLOR")

        # PICTO_SHAPE
        shape_map = {
            "Cercle": "circle",
            "Carré": "square",
            "Triangle": "triangle",
            "Croix": "cross",
            "X": "cross2",
            "Losange": "diamond",
            "Étoile": "star",
            "Coeur": "heart",
        }

        # Store enum values as integers (Qgis.MarkerShape is an IntEnum)
        self.fe.add_value_map("PICTO_SHAPE", {"map": [{label: shape} for label, shape in shape_map.items()]})
        self.fe.set_reuse_last_value("PICTO_SHAPE")

    def _style(self):
        sym_layer = QgsSimpleMarkerSymbolLayer()
        sym_layer.setDataDefinedProperty(QgsSymbolLayer.PropertyFillColor, QgsProperty.fromExpression('"PICTO_COLOR"'))
        sym_layer.setDataDefinedProperty(QgsSymbolLayer.PropertyName, QgsProperty.fromExpression('"PICTO_SHAPE"'))

        # Wrap in a symbol (container)
        symbol = QgsSymbol.defaultSymbol(self.layer.geometryType())
        symbol.deleteSymbolLayer(0)
        symbol.appendSymbolLayer(sym_layer)

        # Apply to layer
        self.layer.setRenderer(QgsSingleSymbolRenderer(symbol))
        self.layer.triggerRepaint()
