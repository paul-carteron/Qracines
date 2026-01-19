from typing import Any

from qgis.core import QgsProject,QgsExpressionContextUtils, QgsVectorLayer

from collections import defaultdict

def get_global_variable(name: str) -> Any:
    """Return the value of a *global* expression variable."""
    return QgsExpressionContextUtils.globalScope().variable(name)

def set_global_variable(name: str, value: Any) -> None:
    """Set a global expression variable (string/int/float/bool)."""
    QgsExpressionContextUtils.setGlobalVariable(name, value)
    return None

def get_project_variable(name: str) -> Any:
    """Return a project-level variable or `None` if missing."""
    return QgsExpressionContextUtils.projectScope(QgsProject.instance()).variable(name)

def set_project_variable(name: str, value: Any) -> None:
    """
    Set a project-level variable.

    Anything that isn’t str/int/float/bool is auto-converted to str to avoid
    QVariant type errors.
    """
    _safe_set(QgsExpressionContextUtils.setProjectVariable, name, value)

def _safe_set(setter, name: str, value: Any) -> None:
    if not isinstance(value, (str, int, float, bool)):
        print(f"[Warn] {name!r}: {type(value).__name__} → str")
        value = str(value)
    try:
        # setter signature: (project, name, value) OR (name, value) for global
        setter(QgsProject.instance(), name, value)  # *ignored* by global setter
    except Exception as err:
        print(f"[Error] cannot set {name!r}: {value!r}  →  {err}")

# Ces fonctions devraient plutôt être dans projet_settings dialog car spécifiques à ce module

# Fonction pour City & Owner
def get_grouped_values_from_shapefile(shapefile_path, value_field, filter_field, surface_field):

    # Load shapefile as a QGIS vector layer
    layer = QgsVectorLayer(str(shapefile_path), "input_layer", "ogr")
    if not layer.isValid():
        raise RuntimeError(f"Cannot load shapefile: {str(shapefile_path)}")
    
    # Dictionnaire pour regrouper les valeurs
    group_dict = defaultdict(list)
    
    # Handle "no filter" case
    use_filter = filter_field is not None
    no_filter_label = "No Filter"
    
    # Iterate over features in the layer
    for feature in layer.getFeatures():
        # Filter value
        if use_filter:
            filter_value = feature[filter_field]
        else:
            filter_value = no_filter_label

        value = feature[value_field]
        surface = feature[surface_field]

        group_dict[filter_value].append((value, surface))

    result_list = []
    
    # Aggregate values per group
    for group, values in group_dict.items():

        aggregated_values = defaultdict(float)

        for value, surface in values:
            aggregated_values[value] += surface

        # Sort by descending surface
        sorted_values = sorted(
            aggregated_values.items(),
            key=lambda x: x[1],
            reverse=True
        )

        value_list = [v[0] for v in sorted_values]

        # Build string with ", " and " & "
        if len(value_list) == 2:
            result_string = f"{value_list[0]} & {value_list[1]}"
        elif len(value_list) > 2:
            result_string = f"{', '.join(value_list[:-1])} & {value_list[-1]}"
        elif len(value_list) == 1:
            result_string = value_list[0]
        else:
            continue

        # Append group label if filtering is used
        if use_filter:
            result_list.append(f"{result_string} ({group})")
        else:
            result_list.append(result_string)

    return "; ".join(result_list)

# Fonction pour Surface
def sum_surface_from_shapefile(shapefile_path, surface_field, filter_field=None, filter_value=None):
    # Load layer
    layer = QgsVectorLayer(str(shapefile_path), "input_layer", "ogr")
    if not layer.isValid():
        raise RuntimeError(f"Cannot load shapefile: {str(shapefile_path)}")

    total = 0.0
    found = False

    for feature in layer.getFeatures():

        # Apply filter if requested
        if filter_field is not None and filter_value is not None:
            if feature[filter_field] != filter_value:
                continue

        surface = feature[surface_field]
        if surface is not None:
            total += surface
            found = True

    # If filtering was requested but no matching feature was found
    if filter_field is not None and filter_value is not None and not found:
        return None

    return total
  
def get_formated_surface(surface_boisee, surface_non_boisee):
    surface_totale = surface_boisee + surface_non_boisee

    if surface_non_boisee > 0:
        surface_totale_ha = round(surface_totale / 10000, 4)
        surface_boisee_ha = round(surface_boisee / 10000, 4)
        formatted_surface = (
            f"Surface totale: {surface_totale_ha:.4f} ha | Surface boisée: {surface_boisee_ha:.4f} ha"
        )
    else:
        hectares = round(surface_boisee // 10000)
        ares = round((surface_boisee % 10000) // 100)
        centiares = round(surface_boisee % 100)
        formatted_surface = (
            f"Surface totale: {hectares} ha {ares:02} a {centiares:02} ca"
        )

    return formatted_surface
  



