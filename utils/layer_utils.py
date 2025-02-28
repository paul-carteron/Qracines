from qgis.core import *

class LayerUtils:
    def __init__(self, iface):
        self.iface = iface
        
    # Fonctions d'ouverture de shapefiles
    def add_shp_layers(self, path, foret, layers_path, layers_name, styles_path, grouped, group_name):
        for i in range(len(layers_path)):
            layer_path = path + '/' + foret + layers_path[i]
            layer_name = layers_name[i]
            style_path = style_directory + '/' + styles_path[i]
            layer = QgsVectorLayer(layer_path, layer_name, 'ogr')
            if layer.isValid():
                if grouped==False:
                    QgsProject.instance().addMapLayer(layer)
                if grouped==True:
                    QgsProject.instance().addMapLayer(layer,False)
                    group_name.addLayer(layer)
                layer.loadNamedStyle(style_path)
        pass
    
    # Fonctions d'ouverture de raster
    def add_raster_layers(self, path, foret, layers_path, layers_name, grouped, group_name):
        for i in range(len(layers_path)):
            layer_path = path + '/' + foret + layers_path[i]
            layer_name = layers_name[i]
            layer = QgsRasterLayer(layer_path, layer_name)
            if layer.isValid():
                if grouped==False:
                    QgsProject.instance().addMapLayer(layer)
                if grouped==True:
                    QgsProject.instance().addMapLayer(layer,False)
                    group_name.addLayer(layer)
        pass
      
    # Fonctions d'application de style
    def style_on_layer(self, layer_name):
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        style_path = style_directory + '/'+ layer_name + '.qml'
        if layer.loadNamedStyle(style_path):
            layer.triggerRepaint()
        pass

    def style_on_layers(self, layers):
        for layer in layers:
            style_on_layer(layer)
        pass
      
    # Fonctions de visibilité des couches
    def visibility_on_layer(self, layer_name, visibility):
        layer = QgsProject.instance().mapLayersByName(layer_name)
        if layer:
            layer = layer[0]
            layer_node = QgsProject.instance().layerTreeRoot().findLayer(layer.id())
            if layer_node:
                layer_node.setItemVisibilityChecked(visibility)
        pass

    def visibility_on_layers(self, layers, visibility):
        for layer in layers:
            visibility_on_layer(layer, visibility)
        pass
      
    # Fonction zoom sur emprise
    def zoom_on_layer(self, layer_name):
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        canvas = iface.mapCanvas()
        extent = layer.extent()
        canvas.setExtent(extent)
        pass
      
    # Réduire les couches  
    def replier_groupes(self, node):
      if isinstance(node, QgsLayerTreeGroup):
          node.setExpanded(False)
          for enfant in node.children():
              replier_groupes(enfant)
      pass
