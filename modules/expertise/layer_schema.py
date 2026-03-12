
from qgis.PyQt.QtCore import QVariant

EXPERTISE_LAYERS = {
  
    "Placette": {
        "geometry": "Point",
        "fields": [
            ("UUID", QVariant.String),
            ("COMPTEUR", QVariant.LongLong),
            ("PLA_RMQ", QVariant.String),
            # Peuplement
            ("PLTM_PARCELLE", QVariant.String),
            ("PLTM_STRATE", QVariant.String),
            ("PLTM_TYPE", QVariant.String),
            # Taillis
            ("TSE_STERE_HA", QVariant.String),
        ],
    },

    "Transect": {
        "geometry": "Point",
        "fields": [
            ("UUID", QVariant.String),
            ("TR_PARCELLE", QVariant.String),
            ("TR_STRATE", QVariant.String),
            ("TR_ESSENCE_ID", QVariant.String),
            ("TR_ESSENCE_SECONDAIRE_ID", QVariant.String),
            ("TR_DIAMETRE", QVariant.String),
            ("TR_EFFECTIF", QVariant.LongLong),
            ("TR_HAUTEUR", QVariant.String),
        ],
    },

    "Limite": {
        "geometry": "LineString",
        "fields": [
            ("LIMITE_TYPE", QVariant.String), 
            ("LIMITE_RMQ", QVariant.String)
        ],
    },

    "Gha": {
        "fields": [
            ("UUID", QVariant.String),
            ("GHA_ESSENCE_ID", QVariant.String),
            ("GHA_ESSENCE_SECONDAIRE_ID", QVariant.String),
            ("GHA_G", QVariant.Int),
        ],
    },

    "Tse": {
        "fields": [
            ("UUID", QVariant.String),
            ("TSE_ESSENCE_ID", QVariant.String),
            ("TSE_ESSENCE_SECONDAIRE_ID", QVariant.String),
        ],
    },

    "Va": {
        "fields": [
            ("UUID", QVariant.String),
            ("VA_ESSENCE_ID", QVariant.String),
            ("VA_ESSENCE_SECONDAIRE_ID", QVariant.String),
            ("VA_AGE_APP", QVariant.LongLong),
            ("VA_TX_TROUEE", QVariant.LongLong),
            ("VA_TX_HA", QVariant.Double),
            ("CUMUL_TX_VA", QVariant.Double)
        ],
    },

    "Reg": {
        "fields": [
            ("UUID", QVariant.String),
            ("REG_ESSENCE_ID", QVariant.String),
            ("REG_ESSENCE_SECONDAIRE_ID", QVariant.String),
            ("REG_STADE", QVariant.String),
            ("REG_ETAT", QVariant.String),
        ],
    },
}