from qgis.PyQt.QtCore import QMetaType

EXPERTISE_LAYERS = {
  
    "placette": {
        "geometry": "Point",
        "fields": [
            ("UUID", QMetaType.Type.QString),
            ("COMPTEUR", QMetaType.Type.LongLong),
            ("PLA_RMQ", QMetaType.Type.QString),
            # Peuplement
            ("PLTM_PARCELLE", QMetaType.Type.QString),
            ("PLTM_STRATE", QMetaType.Type.QString),
            ("PLTM_TYPE", QMetaType.Type.QString),
            # Taillis
            ("TSE_STERE_HA", QMetaType.Type.QString),
        ],
    },

    "transect": {
        "geometry": "Point",
        "fields": [
            ("UUID", QMetaType.Type.QString),
            ("TR_PARCELLE", QMetaType.Type.QString),
            ("TR_STRATE", QMetaType.Type.QString),
            ("TR_ESSENCE_ID", QMetaType.Type.QString),
            ("TR_ESSENCE_SECONDAIRE_ID", QMetaType.Type.QString),
            ("TR_DIAMETRE", QMetaType.Type.QString),
            ("TR_EFFECTIF", QMetaType.Type.LongLong),
            ("TR_HAUTEUR", QMetaType.Type.QString),
        ],
    },

    "limite": {
        "geometry": "LineString",
        "fields": [
            ("LIMITE_TYPE", QMetaType.Type.QString), 
            ("LIMITE_RMQ", QMetaType.Type.QString),
        ],
    },

    "gha": {
        "fields": [
            ("UUID", QMetaType.Type.QString),
            ("GHA_ESSENCE_ID", QMetaType.Type.QString),
            ("GHA_ESSENCE_SECONDAIRE_ID", QMetaType.Type.QString),
            ("GHA_G", QMetaType.Type.Int),
        ],
    },

    "tse": {
        "fields": [
            ("UUID", QMetaType.Type.QString),
            ("TSE_ESSENCE_ID", QMetaType.Type.QString),
            ("TSE_ESSENCE_SECONDAIRE_ID", QMetaType.Type.QString),
        ],
    },

    "va": {
        "fields": [
            ("UUID", QMetaType.Type.QString),
            ("VA_ESSENCE_ID", QMetaType.Type.QString),
            ("VA_ESSENCE_SECONDAIRE_ID", QMetaType.Type.QString),
            ("VA_AGE_APP", QMetaType.Type.LongLong),
            ("VA_TX_TROUEE", QMetaType.Type.LongLong),
            ("VA_TX_HA", QMetaType.Type.Double),
            ("CUMUL_TX_VA", QMetaType.Type.Double),
        ],
    },

    "reg": {
        "fields": [
            ("UUID", QMetaType.Type.QString),
            ("REG_ESSENCE_ID", QMetaType.Type.QString),
            ("REG_ESSENCE_SECONDAIRE_ID", QMetaType.Type.QString),
            ("REG_STADE", QMetaType.Type.QString),
            ("REG_ETAT", QMetaType.Type.QString),
        ],
    },
}