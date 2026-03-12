from qgis.PyQt.QtCore import QVariant

TREE_MARKING_LAYERS = {

    "Param": {
        "fields": [
        ("fid", QVariant.Int),
        ("TYPE", QVariant.String),
        ("LOT", QVariant.String),
        ("PARCELLE", QVariant.String),
        ("SURFACE", QVariant.Double),
        ("MARQUAGE_BO", QVariant.String),
        ("COULEUR_BO", QVariant.String),
        ("MARQUAGE_BI", QVariant.String),
        ("COULEUR_BI", QVariant.String),
        ("MARQUE", QVariant.String),
        ],
    },

    "Arbres": {
        "geometry": "Point",
        "fields": [
        ("fid", QVariant.Int),
        ("ID_CODE", QVariant.String),
        ("UUID", QVariant.String),
        ("LOT", QVariant.String),
        ("PARCELLE", QVariant.String),
        ("ESSENCE_ID", QVariant.String),
        ("ESSENCE_SECONDAIRE_ID", QVariant.String),
        ("DIAMETRE", QVariant.String),
        ("EFFECTIF", QVariant.LongLong),
        ("HAUTEUR", QVariant.String),
        ("FAVORI", QVariant.Bool),
        ("OBSERVATION", QVariant.String),
        ("COMPTEUR", QVariant.LongLong),
        ],
    },
}
       