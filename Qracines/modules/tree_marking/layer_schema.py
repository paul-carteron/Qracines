from qgis.PyQt.QtCore import QMetaType

TREE_MARKING_LAYERS = {

    "Lot": {
        "fields": [
            ("FOREST_ID", QMetaType.Type.QString),
            ("TYPE", QMetaType.Type.QString),
            ("LOT", QMetaType.Type.QString),
            ("PARCELLE", QMetaType.Type.QString),
            ("SURFACE", QMetaType.Type.Double),
            ("MARQUAGE_BO", QMetaType.Type.QString),
            ("COULEUR_BO", QMetaType.Type.QString),
            ("MARQUAGE_BI", QMetaType.Type.QString),
            ("COULEUR_BI", QMetaType.Type.QString),
            ("MARQUE", QMetaType.Type.QString),
        ],
    },

    "Param": {
        "fields": [
            ("HMIN", QMetaType.Type.Int),
            ("HMAX", QMetaType.Type.Int),
            ("DMIN", QMetaType.Type.Int),
            ("DMAX", QMetaType.Type.Int),
        ],
    },

    "Arbres": {
        "geometry": "Point",
        "fields": [
            ("UUID", QMetaType.Type.QString),
            ("PARCELLE", QMetaType.Type.QString),
            ("ESSENCE_ID", QMetaType.Type.QString),
            ("ESSENCE_SECONDAIRE_ID", QMetaType.Type.QString),
            ("DIAMETRE", QMetaType.Type.Int),
            ("EFFECTIF", QMetaType.Type.LongLong),
            ("HAUTEUR", QMetaType.Type.Int),
            ("FAVORI", QMetaType.Type.Bool),
            ("OBSERVATION", QMetaType.Type.QString),
            ("COMPTEUR", QMetaType.Type.LongLong),
        ],
    },

    "lst_hauteur": {
        "fields": [
            ("VALEUR", QMetaType.Type.Int),
        ],
    },

    "lst_diam": {
        "fields": [
            ("VALEUR", QMetaType.Type.Int),
        ],
    },
}