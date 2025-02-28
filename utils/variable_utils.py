from qgis.core import *
from qgis.utils import iface

class VariableUtils:
    def __init__(self, iface):
        self.iface = iface
        
    # Fonctions de récupération des valeurs d'un champ    
    def values_from_layer(self, layer_name, field_name):
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        unique_values = set()
        for feature in layer.getFeatures():
            value = feature[field_name]
            unique_values.add(value)
        sorted_values = sorted(unique_values)
        concatenated_values = ' & '.join(map(str, sorted_values))
        number_of_values = len(sorted_values)
        return concatenated_values, number_of_values
        pass
      
    # Fonction de récupération des communes  
    def concatenate_com_per_dep(self, layer_name):
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        dep_com_dict = {}
        for feature in layer.getFeatures():
            dep_value = feature['DEP_CODE']
            com_value = feature['COM_NOM']
            if dep_value not in dep_com_dict:
                dep_com_dict[dep_value] = set()  # Utilisation d'un set pour garantir l'unicité
                dep_com_dict[dep_value].add(com_value)
        forest_city_parts = []
        for dep, com_values in dep_com_dict.items():
            concatenated_com = ', '.join(sorted(map(str, com_values)))
            forest_city_parts.append(f"{concatenated_com} ({dep})")
        forest_city = ' & '.join(forest_city_parts)
        return forest_city
      
    # Fonctions de somme d'un champ filtré sur un autre
    def sum_from_layer(self, layer_name, field_to_sum, filter_field, filter_value):
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        filter_expression = f'"{filter_field}" = \'{filter_value}\''
        request = QgsFeatureRequest().setFilterExpression(filter_expression)
        total_sum = 0.0
        for feature in layer.getFeatures(request):
            value = feature[field_to_sum]
            if isinstance(value, float):
                total_sum += float(value)
        return total_sum
            
    # Fonction pour ajouter variable
    def set_project_variable(self, variable_name, value):
        project = QgsProject.instance()
        exists = QgsExpressionContextUtils.projectScope(project).variable(variable_name)
        if not exists:
            QgsExpressionContextUtils.setProjectVariable(project, variable_name, value)
            
    def set_global_variable(variable_name, value):
        settings = QgsSettings()
        settings.setValue(variable_name, value)
        
    def get_global_variable(variable_name):
        settings = QgsSettings()
        return settings.value(variable_name, "")
      
