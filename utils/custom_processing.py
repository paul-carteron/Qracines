import processing

def calculate_essence_id(layer, f_ess_id, f_ess_sec_id, f_name='ESSENCE_ID'):
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

def merge_with_ess(layer, ess, f_ess_id ='ESSENCE_ID'):
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
