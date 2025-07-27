from pathlib import Path
from qgis.utils import iface
from qgis.core import *
from qgis.PyQt.QtXml import QDomDocument
import processing

from .path_manager import get_display_name, get_default, get_type

def compute_map_info(layer_name: str,
                     map_scale: int = 7500,
                     buffer_distance: float = 15
                     ) -> dict:
    """
    À partir d'une couche polygonale, génère un tampon, sépare les multiparts,
    conserve la plus grande entité, retourne sa bbox, son orientation et le format papier adapté.
    """
    project = QgsProject.instance()
    display_name = get_display_name(layer_name)
    layers = project.mapLayersByName(display_name)

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

    return {
        "bbox": bbox,
        "orientation": orientation,
        "format_papier": best_format,
        "surface": geom.area(),
        "geometry": geom
    }

def import_layout_from_template(info: dict, models_directory: Path) -> QgsPrintLayout:
    """
    Importe un layout .qpt en fonction des infos calculées (format, orientation).
    """
    models_directory = Path(models_directory)
    fmt = info["format_papier"]
    orientation = info["orientation"]
    
    # Chemin du QPT
    qpt_path = models_directory / f"{fmt}_{orientation}.qpt"
    
    # Si le fichier n'existe pas et qu'on est en landscape, fallback en portrait
    if not qpt_path.exists() and orientation.lower() == "landscape":
        orientation = "portrait"
        qpt_path = models_directory / f"{fmt}_{orientation}.qpt"
        
    # Chargement du layout
    if qpt_path.exists():
        project = QgsProject.instance()
        layout = QgsPrintLayout(project)
        layout.initializeDefaults()
    
        template_doc = QDomDocument()
        with qpt_path.open('r', encoding='utf-8') as f:
            template_doc.setContent(f.read())
    
        context = QgsReadWriteContext()
        layout.loadFromTemplate(template_doc, context)
    
        layout.setName(f"{fmt}_{orientation}")
        project.layoutManager().addLayout(layout)
    
        return layout
      
    else:
        print(f"Modèle QPT introuvable : {qpt_path}")

def get_main_map_item(layout: QgsPrintLayout) -> QgsLayoutItemMap:
    """
    Récupère le premier QgsLayoutItemMap du layout.
    """
    for item in layout.items():
        if isinstance(item, QgsLayoutItemMap):
            return item
    raise ValueError("Aucune carte (QgsLayoutItemMap) trouvée dans le layout.")

def configure_layout(layout: QgsPrintLayout,
                     geometry: QgsGeometry,
                     project: str,
                     type_: str,
                     hide_legend_names: bool = True
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
    theme = get_default(project, "theme")
    scale = get_default(project, "scale")
    legend_layers = get_type(project, type_).get('legend_layers')

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
    
    if legend_layers:
        add_layer_to_legend(layout, 'legend', *legend_layers, hide_name=hide_legend_names)
    
        
def add_layer_to_legend(layout, legend_id='legend', *keys, hide_name=True):
    legend = layout.itemById(legend_id)
    if not legend:
        raise ValueError(f"Élément légende '{legend_id}' non trouvé")

    root = legend.model().rootGroup()  # Récupère le groupe racine de la légende

    for key in keys:
        print(f"key '{key}' in '{keys}'")
        display_name = get_display_name(key)
        print(f"display_name to find '{display_name}'")
        layers = QgsProject.instance().mapLayersByName(display_name)
        if not layers:
            raise ValueError(f"La couche '{display_name}' est introuvable dans le projet")
    
        layer = layers[0]
        print(f"layer to find '{layer}'")
        
        # Vérifier si la couche existe déjà dans la légende pour éviter les doublons
        existing_layers = [node.layerId() for node in root.findLayers()]
        if layer.id() in existing_layers:
            print(f"La couche '{display_name}' est déjà dans la légende")
            continue

        # Ajouter la couche dans la légende
        legend_node = root.addLayer(layer)

        # Masquer le nom si demandé
        if hide_name:
            legend_node.setName("")

    legend.refresh()
