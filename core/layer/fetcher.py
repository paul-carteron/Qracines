from qgis.core import QgsProject


class LayerFetcher:
    @staticmethod
    def get_layer(layer_name):
        layers = QgsProject.instance().mapLayersByName(layer_name)
        if not layers:
            raise ValueError(f"Layer '{layer_name}' not found.")
        return layers[0]

    @staticmethod
    def get_relation_by_name(relation_name):
        manager = QgsProject.instance().relationManager()
        matches = manager.relationsByName(relation_name)
        return matches[0] if matches else None
