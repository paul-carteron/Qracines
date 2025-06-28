from pathlib import Path
from qgis.core import *
from qgis.PyQt.QtXml import QDomDocument
import processing

from .path_manager import get_display_name

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
    qpt_path = models_directory / f"{fmt}_{orientation}.qpt"

    if not qpt_path.exists():
        raise FileNotFoundError(f"Modèle QPT introuvable : {qpt_path}")

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
                     map_theme: str = None,
                     fixed_scale: int = None
                     ) -> None:
    """
    Paramètre dynamiquement le layout : zoom sur une géométrie et applique un thème de carte si spécifié.

    :param layout: Layout à configurer
    :param geometry: QgsGeometry servant au zoom
    :param map_theme: Nom du thème de carte (doit exister dans le projet)
    :param fixed_scale: Échelle fixe à appliquer (sinon zoom auto)
    """
    from qgis.core import QgsProject, QgsLayoutItemMap

    map_items = [item for item in layout.items() if isinstance(item, QgsLayoutItemMap)]

    if not map_items:
        raise ValueError("Aucune carte (QgsLayoutItemMap) trouvée dans le layout.")

    map_item = map_items[0]  # première carte trouvée

    # Appliquer un thème de carte s'il est spécifié
    if map_theme:
        theme_collection = QgsProject.instance().mapThemeCollection()
        if map_theme not in theme_collection.mapThemes():
            raise ValueError(f"Le thème de carte '{map_theme}' est introuvable dans le projet.")

        map_item.setFollowVisibilityPreset(True)
        map_item.setFollowVisibilityPresetName(map_theme)

    # Zoom sur la géométrie
    if fixed_scale:
        map_item.setExtent(geometry.boundingBox())
        map_item.setScale(fixed_scale)
    else:
        map_item.zoomToExtent(geometry.boundingBox())
