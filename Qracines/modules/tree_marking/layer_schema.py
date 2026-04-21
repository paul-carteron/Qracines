from qgis.PyQt.QtCore import QVariant

TREE_MARKING_LAYERS = {

    "Param": {
        "fields": [
        ("FOREST_ID", QVariant.String),
        ("TYPE", QVariant.String),
        ("LOT", QVariant.String),
        ("PARCELLE", QVariant.String),
        ("SURFACE", QVariant.Double),
        ("MARQUAGE_BO", QVariant.String),
        ("COULEUR_BO", QVariant.String),
        ("MARQUAGE_BI", QVariant.String),
        ("COULEUR_BI", QVariant.String),
        ("MARQUE", QVariant.String),
        ("HMIN", QVariant.Int),
        ("HMAX", QVariant.Int),
        ("DMIN", QVariant.Int),
        ("DMAX", QVariant.Int),
        ],
    },

    "Arbres": {
        "geometry": "Point",
        "fields": [
        ("ID_CODE", QVariant.String),
        ("UUID", QVariant.String),
        ("PARCELLE", QVariant.String),
        ("ESSENCE_ID", QVariant.String),
        ("ESSENCE_SECONDAIRE_ID", QVariant.String),
        ("DIAMETRE", QVariant.Int),
        ("EFFECTIF", QVariant.LongLong),
        ("HAUTEUR", QVariant.Int),
        ("FAVORI", QVariant.Bool),
        ("OBSERVATION", QVariant.String),
        ("COMPTEUR", QVariant.LongLong),
        ],
    },

    "lst_hauteur": {
        "fields": [
        ("VALEUR", QVariant.Int),
        ],
    },

    "lst_diam": {
        "fields": [
        ("VALEUR", QVariant.Int),
        ],
    },
}
       