from pathlib import Path
from qgis.utils import iface
from qgis.core import *
from qgis.PyQt.QtXml import QDomDocument
import processing
from qgis.PyQt.QtWidgets import QApplication

from .path_manager import get_display_name, get_project_default, get_type, get_project_legends
from .variable_utils import get_global_variable

def compute_map_info(
        layer_key: str,
        map_scale: int = 7500,
        buffer_distance: float = 15
        ) -> dict:
    """
    À partir d'une couche polygonale, génère un tampon, sépare les multiparts,
    conserve la plus grande entité, retourne sa bbox, son orientation et le format papier adapté.
    """

    display_name = get_display_name(layer_key)
    print(display_name)
    layers = QgsProject.instance().mapLayersByName(display_name)

    if not layers:
        raise ValueError(f"La couche '{display_name}' est introuvable dans le projet.")
    input_layer = layers[0]

    if input_layer.geometryType() != QgsWkbTypes.PolygonGeometry:
        raise ValueError("La couche d'entrée doit être une couche polygonale.")

    # 1. Tampon avec dissolve
    buffer_result = processing.run("native:buffer", {
        'INPUT': input_layer,
        'DISTANCE': buffer_distance,
        'SEGMENTS': 8,
        'DISSOLVE': True,
        'OUTPUT': 'memory:buffered'
    })
    buffered = buffer_result['OUTPUT']

    # 2. Multipart → singleparts
    singleparts_result = processing.run("native:multiparttosingleparts", {
        'INPUT': buffered,
        'OUTPUT': 'memory:singleparts'
    })
    singleparts = singleparts_result['OUTPUT']

    # 3. Identifier l'entité avec la plus grande surface
    max_feat = max(singleparts.getFeatures(), key=lambda f: f.geometry().area(), default=None)

    if max_feat is None:
        raise ValueError("Aucune entité valide trouvée après traitement.")

    geom = max_feat.geometry()
    bbox = geom.boundingBox()
    width = bbox.width()
    height = bbox.height()
    orientation = 'portrait' if height > width else 'landscape'

    # 4. Taille des formats papier à l’échelle donnée (en mètres)
    formats_mm = {
        "A4": (210, 297),
        "A3": (297, 420),
        "A2": (420, 594),
        "A1": (594, 841),
        "A0": (841, 1189)
    }

    def scaled_size(mm_size):
        return (mm_size[0] / 1000 * map_scale,
                mm_size[1] / 1000 * map_scale)

    def bbox_fits(size, orientation):
        fw, fh = size
        return (fw >= width and fh >= height) if orientation == 'portrait' else (fw >= height and fh >= width)

    best_format = next(
        (fmt for fmt, mm in formats_mm.items() if bbox_fits(scaled_size(mm), orientation)),
        "A0+"
    )
    
    print(f"Template: {best_format}_{orientation}")

    return {
        "bbox": bbox,
        "orientation": orientation,
        "format_papier": best_format,
        "surface": geom.area(),
        "geometry": geom
    }

def import_layout_from_template(format, orientation = "portrait") -> QgsPrintLayout | None:
    """
    Importe un layout .qpt en fonction des infos calculées (format, orientation).
    Retourne None si échec.
    """
    models_directory = Path(get_global_variable('models_directory'))

    # Chemin du QPT
    qpt_path = models_directory / f"{format}_{orientation}.qpt"

    # Fallback portrait si landscape introuvable
    if not qpt_path.exists() and orientation.lower() == "landscape":
        orientation = "portrait"
        qpt_path = models_directory / f"{format}_{orientation}.qpt"

    try:
        if not qpt_path.exists():
            print(f"Template introuvable : {qpt_path}")

        project = QgsProject.instance()
        layout = QgsPrintLayout(project)
        layout.initializeDefaults()

        template_doc = QDomDocument()
        with qpt_path.open('r', encoding='utf-8') as f:
            template_doc.setContent(f.read())

        context = QgsReadWriteContext()
        layout.loadFromTemplate(template_doc, context)

        layout.setName(f"{format}_{orientation}")
        project.layoutManager().addLayout(layout)

        return layout

    except Exception as e:
        return None
    
def configure_layout(layout: QgsPrintLayout,
                     project: str,
                     hide_legend_names: bool = False
                     ) -> None:
    """
    Configure dynamiquement le layout :
    - Zoom sur une géométrie
    - Applique un thème de carte
    - Met à jour la légende si spécifiée dans le YAML

    :param layout: Layout à configurer
    :param geometry: QgsGeometry servant au zoom
    :param project: Nom du projet (clé YAML)
    :param type_ (str): type de données ('wooded', 'unwooded', etc.)
    :param hide_legend_names: Masquer les noms des couches dans la légende
    """

    # Récupération des paramètres YAML
    default = get_project_default(project)
    theme = default.get("composer_theme")
    scale = default.get("scale")

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
        theme_collection = QgsProject.instance().mapThemeCollection()
        if theme not in theme_collection.mapThemes():
            raise ValueError(f"Le thème de carte '{theme}' est introuvable dans le projet.")

        map_item.setFollowVisibilityPreset(True)
        map_item.setFollowVisibilityPresetName(theme)

    # Appliquer une échelle fixe si définie
    if scale:
        map_item.setScale(scale)

    # Ajouter la légende si spécifiée
    legends = get_project_legends(project)
    for l in legends:
        legend_name = l.get("name")
        legend_layers = l.get("layers")
        add_layer_to_legend(layout, legend_name, *legend_layers, hide_name=hide_legend_names)

    # Complète la table
    pf_display_name = get_display_name("pf_polygon")
    layers = QgsProject.instance().mapLayersByName(pf_display_name)
    if layers:
      configure_attribute_table(
        layout,
        table_id = "table1",
        layer_key = "pf_polygon",
        fields = ["N_PARFOR", "SURF_COR"],
        map_id = "map1",
        filter_expression = '"N_PARFOR" <> \'00\''
      )
        
def add_layer_to_legend(layout: QgsPrintLayout,
                        legend_id: str, 
                        *layer_keys: list, 
                        hide_name: bool = True, 
                        map_id: str = None):
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
        layers = QgsProject.instance().mapLayersByName(display_name)
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

def configure_attribute_table(layout: QgsPrintLayout, 
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
    layers = QgsProject.instance().mapLayersByName(display_name)
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


def close_all_layout_designers() -> int:
    """
    Close all open QGIS Layout Designer windows.
    Returns the number of windows closed.
    """
    closed = 0
    for w in QApplication.topLevelWidgets():
        # Layout Designer windows expose a callable designerInterface()
        di = getattr(w, "designerInterface", None)
        if callable(di):
            try:
                w.close()
                closed += 1
            except Exception:
                pass
    # Flush close events
    QApplication.processEvents()
    print(f"[designer] closed {closed} layout designer window(s).")
    return closed
