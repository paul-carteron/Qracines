from .fetcher import LayerFetcher
from .field_editor import FieldEditor
from .form_builder import FormBuilder
from qgis.core import QgsProject


class LayerManager:
    def __init__(self, layer_name):
        self.layer = LayerFetcher.get_layer(layer_name)
        self.fields = FieldEditor(self.layer)
        self.forms = FormBuilder(self.layer)

    def set_visibility(self, visible: bool):
        node = QgsProject.instance().layerTreeRoot().findLayer(self.layer.id())
        if node:
            node.setItemVisibilityChecked(visible)
