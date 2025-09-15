import processing
import math
from qgis.core import QgsProcessing

def calculate_essence_id(layer, f_ess_id, f_ess_sec_id, f_name='ESSENCE_ID_KEY'):
    """
    Adds a calculated ESSENCE_ID field to a layer by combining two existing fields.

    Parameters
    ----------
    layer : QgsVectorLayer
        The input layer to process.
    f_ess_id : str
        Name of the primary essence ID field (e.g. 'TR_ESSENCE_ID').
    f_ess_sec_id : str
        Name of the secondary essence ID field (e.g. 'TR_ESSENCE_SECONDAIRE_ID').
    f_name : str, optional
        Name of the output field to create. Defaults to 'ESSENCE_ID'.

    Returns
    -------
    QgsVectorLayer
        A memory layer with the new ESSENCE_ID field calculated as:
        - Primary field value if not null or empty
        - Otherwise, secondary field value if not null or empty
        - Cast as integer
    """
    layer_with_ess_id = processing.run("qgis:fieldcalculator", {
        'INPUT': layer,
        'FIELD_NAME': f_name,
        'FIELD_TYPE': 1,
        'FIELD_LENGTH': 50,
        'FIELD_PRECISION': 0,
        'FORMULA': f"""
            to_int(
                coalesce(
                    nullif("{f_ess_id}", ''),
                    nullif("{f_ess_sec_id}", '')
                )
            )
        """,
        'OUTPUT': 'memory:'
    })['OUTPUT']

    return layer_with_ess_id

def merge_with_ess(layer, ess, f_ess_id ='ESSENCE_ID_KEY'):
    layer_with_ess = processing.run("qgis:joinattributestable", {
            'INPUT': layer,
            'FIELD': f_ess_id,
            'INPUT_2': ess,
            'FIELD_2': 'fid',
            'FIELDS_TO_COPY': ['essence', 'code', 'variation', 'type'],  # adjust if field names differ
            'METHOD': 1,  # Take only matching
            'DISCARD_NONMATCHING': False,
            'PREFIX': '',
            'OUTPUT': 'memory:'
        })['OUTPUT']
    return layer_with_ess

def save_as_xlsx(*layers, path):

    processing.run("native:exporttospreadsheet", {
        'LAYERS': list(layers),
        'OUTPUT': str(path),
        'USE_ALIAS': False,
        'FORMATTED_VALUES': False,
        'OVERWRITE': True
    })

    return

def buffer(layer, distance, dissolve = True, segments=8):
    buffered = processing.run("native:buffer", {
        "INPUT": layer,
        "DISTANCE": distance,
        "SEGMENTS": segments,
        "DISSOLVE": dissolve,
        "OUTPUT": "memory:"
        })["OUTPUT"]
    
    return buffered

def multipart_to_singleparts(layer):
    singleparts = processing.run("native:multiparttosingleparts", {
        "INPUT": layer,
        "OUTPUT": "memory:"
        })["OUTPUT"]
    return singleparts

def create_grid(layer, points_per_ha = 1, clip = True):
    if points_per_ha <= 0:
        raise ValueError("points_per_ha must be > 0.")

    spacing = math.sqrt(10000.0 / float(points_per_ha))
    buffered_layer = buffer(layer, spacing, dissolve=True)

    grid = processing.run('native:creategrid', {
        'TYPE': 0,                
        'EXTENT': buffered_layer.extent(),
        'HSPACING': spacing,
        'VSPACING': spacing,
        'HOVERLAY': 0,
        'VOVERLAY': 0,
        'CRS': buffered_layer.crs(),
        'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
    })['OUTPUT']

    if clip:
        grid = processing.run('native:clip', {
            'INPUT': grid,
            'OVERLAY': buffered_layer,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            })['OUTPUT']
    grid.setName("grid")
    return grid