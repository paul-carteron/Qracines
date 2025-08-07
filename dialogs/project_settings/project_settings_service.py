from dataclasses import dataclass
from pathlib import Path

from qgis.core import QgsProject, QgsWkbTypes, QgsPrintLayout, QgsReadWriteContext, QgsLayoutItemMap, QgsRectangle
from qgis.PyQt.QtXml import QDomDocument

from ...utils.variable import get_global_variable
from ...utils.processing import buffer, multipart_to_singleparts
from ...utils.config import get_display_name

# region LAYOUT CREATION
@dataclass
class MapInfo:
    bbox: QgsRectangle
    orientation: str          # 'portrait' | 'landscape'
    paper_format: str         # 'A4', 'A3', …, 'A0+'
    area: float

FORMATS_MM = {"A4": (210, 297), "A3": (297, 420), "A2": (420, 594), "A1": (594, 841), "A0": (841, 1189)}

def _get_layer(project, key):
        name = get_display_name(key)
        try:
            layer = project.mapLayersByName(name)[0]
        except IndexError:
            raise ValueError(f"Couche '{name}' introuvable")
        if layer.geometryType() != QgsWkbTypes.PolygonGeometry:
            raise TypeError("La couche doit être polygonale")
        return layer

def _fits(mm, scale, w, h, orient):
    fw, fh = (mm[0] /1000*scale, mm[1]/1000*scale)
    return (fw >= w and fh >= h) if orient == "portrait" else (fw >= h and fh >= w)

def compute_layout_info(
        info_layer,
        scale : int, 
        buffer_distance: float = 15) -> MapInfo:

    buffered_layer = buffer(info_layer, buffer_distance)
    single_parts_layer = multipart_to_singleparts(buffered_layer)

    feat = max(single_parts_layer.getFeatures(), key=lambda f: f.geometry().area())
    geom = feat.geometry()
    bbox = geom.boundingBox()
    w, h = bbox.width(), bbox.height()
    orient = "portrait" if h > w else "landscape"
    fmt = next((f for f, mm in FORMATS_MM.items() if _fits(mm, scale, w, h, orient)), "A0+")

    return MapInfo(bbox, orient, fmt, geom.area())

def import_layout(project, fmt: str, orient):
    models_dir = Path(get_global_variable('models_directory'))
    qpt = models_dir / f"{fmt}_{orient}.qpt"

    # If orientation doesn't exist, try switch it
    if not qpt.exists():
        fallback_orient = "portrait" if orient.lower() == "landscape" else "landscape"

        qpt = models_dir / f"{fmt}_{fallback_orient}.qpt"
        
        if qpt.exists():
          orient = fallback_orient 
        else:
            raise FileNotFoundError(f"Template introuvable : {fmt}_*.qpt")
    
    manager = project.layoutManager()
    layoutName = f"{fmt}_{orient}"

    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    doc = QDomDocument();  doc.setContent(qpt.read_text("utf-8"))
    layout.loadFromTemplate(doc, QgsReadWriteContext())
    layout.setName(layoutName)
    manager.addLayout(layout)
    return layout
  
# endregion

# region LAYOUT CONFIGURATION
def configure_layout(
        project,
        iface,
        layout: QgsPrintLayout,
        theme: str,
        scale: str,
        legends: list = None,
        hide_legend_names: bool = False
        ) -> None:

    # Récupérer toutes les cartes dans le layout
    all_maps = [item for item in layout.items() if isinstance(item, QgsLayoutItemMap)]
    if not all_maps:
        raise ValueError("Aucune carte (QgsLayoutItemMap) trouvée dans le layout.")

    # Zoom sur l'emprise actuelle du canevas
    for map_item in all_maps:
        map_item.zoomToExtent(iface.mapCanvas().extent())

    # On privilégie la carte "map1" si elle existe
    map_item = next((m for m in all_maps if m.displayName() == "map1"), all_maps[0])

    # Appliquer un thème de carte si défini
    if theme:
        theme_collection = project.mapThemeCollection()
        if theme not in theme_collection.mapThemes():
            raise ValueError(f"Le thème de carte '{theme}' est introuvable dans le projet.")

        map_item.setFollowVisibilityPreset(True)
        map_item.setFollowVisibilityPresetName(theme)

    # Appliquer une échelle fixe si définie
    if scale:
        map_item.setScale(scale)

    # Ajouter la légende si spécifiée
    for l in legends:
        legend_name = l.get("name")
        legend_layers = l.get("layers")
        add_layer_to_legend(project, layout, legend_name, *legend_layers, hide_name=hide_legend_names)

    # Complète la table
    pf_display_name = get_display_name("pf_polygon")
    layers = project.mapLayersByName(pf_display_name)
    if layers:
      configure_attribute_table(
          project,
          layout,
          table_id = "table1",
          layer_key = "pf_polygon",
          fields = ["N_PARFOR", "SURF_COR"],
          map_id = "map1",
          filter_expression = '"N_PARFOR" <> \'00\''
        )
        
def add_layer_to_legend(
        project,
        layout: QgsPrintLayout,
        legend_id: str, 
        *layer_keys: list, 
        hide_name: bool = True, 
        map_id: str = None
        ):
    """
    Ajoute des couches à une légende dans un composeur, avec option de filtrage par contenu visible sur une carte.

    :param layout: QgsPrintLayout
    :param legend_id: ID de l'objet légende dans le composeur
    :param layer_keys: liste de clés logiques de couches à ajouter
    :param hide_name: masque le nom de la couche dans la légende
    :param map_id: ID de l'objet carte (QgsLayoutItemMap) pour filtrer par contenu visible
    """
    legend = layout.itemById(legend_id)
    if not legend:
        raise ValueError(f"Élément légende '{legend_id}' non trouvé")

    root = legend.model().rootGroup()

    for key in layer_keys:
        display_name = get_display_name(key)
        layers = project.mapLayersByName(display_name)
        if layers:
            layer = layers[0]
            existing_layers = [node.layerId() for node in root.findLayers()]
            if layer.id() in existing_layers:
                print(f"La couche '{display_name}' est déjà dans la légende")
                continue
            legend_node = root.addLayer(layer)
            if hide_name:
                legend_node.setName("")

    # Lier la légende à une carte spécifique pour filtrer les entités visibles
    if map_id:
        map_item = layout.itemById(map_id)
        if not isinstance(map_item, QgsLayoutItemMap):
            raise TypeError(f"L'élément '{map_id}' n'est pas une carte (QgsLayoutItemMap)")
        legend.setLinkedMap(map_item)
        legend.setLegendFilterByMapEnabled(True)

    legend.refresh()

def configure_attribute_table(
        project,
        layout: QgsPrintLayout, 
        table_id: str, 
        layer_key: str, 
        fields: list,
        map_id: str = None,
        filter_expression: str = None):
    """
    Configure une table attributaire dans un layout QGIS 3.40.

    :param layout: QgsPrintLayout contenant la table
    :param table_id: ID de la table dans le composeur
    :param layer_key: clé logique de la couche (convertie avec get_display_name)
    :param fields: liste de champs à afficher
    :param show: ne montrer que les entités visibles
    :param filter_expression: expression QGIS pour filtrer les entités (ex: '"N_PARFOR" <> \'00\'')
    :param alignments: dict facultatif pour aligner les colonnes, ex: {'N_PARFOR': Qt.AlignCenter}
    """
    item = layout.itemById(table_id)
    if not item:
        raise ValueError(f"Élément table '{table_id}' non trouvé dans le layout.")

    if isinstance(item, QgsLayoutFrame):
        table = item.multiFrame()
    elif isinstance(item, QgsLayoutItemAttributeTable):
        table = item
    else:
        raise TypeError(f"L'élément '{table_id}' n'est ni une table ni une frame de table.")

    display_name = get_display_name(layer_key)
    layers = project.mapLayersByName(display_name)
    if not layers:
        raise ValueError(f"Aucune couche trouvée avec le nom '{display_name}'")
    layer = layers[0]

    table.setVectorLayer(layer)
    table.setDisplayedFields(fields)
    
    # setDisplayOnlyVisibleFeatures
    if map_id:
      map_item = layout.itemById(map_id)
      if map_item:
        table.setMap(map_item)
        table.setDisplayOnlyVisibleFeatures(True)
    
    # Appliquer le filtre si fourni
    if filter_expression:
        table.setFeatureFilter(filter_expression)
        table.setFilterFeatures(True)

    table.refresh()

# endregion