
from qgis.PyQt.QtCore import QVariant

DIAGNOSTIC_LAYERS = {
    
    "Placette": {
        "geometry": "Point",
        "fields": [
            # placette
            ("fid", QVariant.Int),
            ("UUID", QVariant.String),
            ("COMPTEUR", QVariant.LongLong),
            ("PLT_PARCELLE", QVariant.String),
            ("PLT_TYPE", QVariant.String),
            ("PLT_RICH", QVariant.String),
            ("PLT_SINISTRE", QVariant.Bool),
            ("PLT_ACCESS", QVariant.Bool),
            ("PLT_STADE", QVariant.String),
            ("PLT_DMOY", QVariant.String),
            ("PLT_ELAG", QVariant.String), 
            ("PLT_SANIT", QVariant.String), 
            ("PLT_CLOISO", QVariant.String), 
            ("PLT_MECA", QVariant.String),
            ("PLT_AME", QVariant.String), 
            ("PLT_RMQ", QVariant.String), 
            ("PLT_PHOTO", QVariant.String),
            # Taillis
            ("TSE_DENS", QVariant.String),
            ("TSE_VOL", QVariant.String),
            ("TSE_NATURE", QVariant.String),
            # Valeur avenir
            ("VA_HT", QVariant.String),
            ("VA_TX_TROUEE", QVariant.String),
            ("VA_VEG_CON", QVariant.String),
            ("VA_TX_DEG", QVariant.Double),
            ("VA_PROTECT", QVariant.String),
    ],
    },
    
    "Transect": {
        "geometry": "Point",
        "fields": [
            ("fid", QVariant.Int),
            ("UUID", QVariant.String),
            ("TR_PARCELLE", QVariant.String),
            ("TR_TYPE_ESS", QVariant.String),
            ("TR_ESS",  QVariant.LongLong),
            ("TR_DIAM", QVariant.Int),
            ("TR_EFFECTIF", QVariant.Int),
            ("TR_HAUTEUR", QVariant.Int)
        ],
    },
    
    "Limite": {
        "geometry": "LineString",
        "fields": [
            ("fid", QVariant.Int),
            ("UUID", QVariant.String),
            ("LIMITE_TYPE", QVariant.String), 
            ("LIMITE_RMQ", QVariant.String), 
            ("LIMITE_PHOTO", QVariant.String)
        ],

    },
    
    "Picto": {
        "geometry": "Point",
        "fields": [
            ("fid", QVariant.Int),
            ("UUID", QVariant.String),
            ("PICTO_TYPE", QVariant.String),
            ("PICTO_RMQ", QVariant.String), 
            ("PICTO_PHOTO", QVariant.String),
            ("PICTO_COLOR", QVariant.String),
            ("PICTO_SHAPE", QVariant.String),
        ],
    },
    
    "Gha": {
        "fields": [
            ("fid", QVariant.Int),
            ("UUID", QVariant.String),
            ("GHA_ESS", QVariant.String),
            ("GHA_G", QVariant.Int),
        ],
    },
    
    "Tse": {
        "fields": [
            ("fid", QVariant.Int),
            ("UUID", QVariant.String),
            ("TSE_ESS", QVariant.String),
            ("TSE_DIM", QVariant.String),
        ],
    },
    
    "Va": {
        "fields": [
            ("fid", QVariant.Int),
            ("UUID", QVariant.String),
            ("VA_ESS", QVariant.String),
            ("VA_TX_HA", QVariant.Double),
            ("VA_CUMUL_TX_VA", QVariant.Double)
        ],
    },
    
    "Reg": {
        "fields": [
            ("fid", QVariant.Int),
            ("UUID", QVariant.String),
            ("REG_ESS", QVariant.String),
            ("REG_STADE", QVariant.String),
            ("REG_ETAT", QVariant.String),
        ],
    },
},