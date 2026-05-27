from qgis.PyQt.QtCore import QMetaType

DIAGNOSTIC_LAYERS = {
    
    "Placette": {
        "geometry": "Point",
        "fields": [
            # Général
            ("fid", QMetaType.Type.Int),
            ("UUID", QMetaType.Type.QString),
            ("COMPTEUR", QMetaType.Type.LongLong),
            ("PLT_TYPE", QMetaType.Type.QString),
            ("PLT_STADE", QMetaType.Type.QString),
            ("PLT_AME", QMetaType.Type.QString), 
            ("PLT_RMQ", QMetaType.Type.QString), 
            ("PLT_PHOTO", QMetaType.Type.QString),
            # Peuplement
            ("PLT_RICH", QMetaType.Type.QString),
            ("PLT_STRUCTURE", QMetaType.Type.QString),
            ("PLT_DMOY", QMetaType.Type.QString),
            ("PLT_CLOISO", QMetaType.Type.QString), 
            ("PLT_ELAG", QMetaType.Type.QString), 
            ("PLT_SANIT", QMetaType.Type.QString), 
            ("PLT_MECA", QMetaType.Type.QString),
            ("PLT_SINISTRE", QMetaType.Type.Bool),
            ("PLT_ACCESS", QMetaType.Type.Bool),
            # Taillis
            ("TSE_DENS", QMetaType.Type.QString),
            ("TSE_VOL", QMetaType.Type.QString),
            ("TSE_NATURE", QMetaType.Type.QString),
            # Valeur avenir
            ("VA_HT", QMetaType.Type.QString),
            ("VA_TX_TROUEE", QMetaType.Type.QString),
            ("VA_VEG_CON", QMetaType.Type.QString),
            ("VA_TX_DEG", QMetaType.Type.Double),
            ("VA_PROTECT", QMetaType.Type.QString),
        ],
    },
    
    "Transect": {
        "geometry": "Point",
        "fields": [
            ("fid", QMetaType.Type.Int),
            ("UUID", QMetaType.Type.QString),
            ("TR_PARCELLE", QMetaType.Type.QString),
            ("TR_TYPE_ESS", QMetaType.Type.QString),
            ("TR_ESS", QMetaType.Type.LongLong),
            ("TR_DIAM", QMetaType.Type.Int),
            ("TR_EFFECTIF", QMetaType.Type.Int),
            ("TR_HAUTEUR", QMetaType.Type.Int),
        ],
    },
    
    "Limite": {
        "geometry": "LineString",
        "fields": [
            ("fid", QMetaType.Type.Int),
            ("UUID", QMetaType.Type.QString),
            ("LIMITE_TYPE", QMetaType.Type.QString), 
            ("LIMITE_RMQ", QMetaType.Type.QString), 
            ("LIMITE_PHOTO", QMetaType.Type.QString),
        ],
    },
    
    "Picto": {
        "geometry": "Point",
        "fields": [
            ("fid", QMetaType.Type.Int),
            ("UUID", QMetaType.Type.QString),
            ("PICTO_TYPE", QMetaType.Type.QString),
            ("PICTO_RMQ", QMetaType.Type.QString), 
            ("PICTO_PHOTO", QMetaType.Type.QString),
            ("PICTO_COLOR", QMetaType.Type.QString),
            ("PICTO_SHAPE", QMetaType.Type.QString),
        ],
    },
    
    "Gha": {
        "fields": [
            ("fid", QMetaType.Type.Int),
            ("UUID", QMetaType.Type.QString),
            ("GHA_ESS", QMetaType.Type.QString),
            ("GHA_G", QMetaType.Type.Int),
        ],
    },
    
    "Tse": {
        "fields": [
            ("fid", QMetaType.Type.Int),
            ("UUID", QMetaType.Type.QString),
            ("TSE_ESS", QMetaType.Type.QString),
            ("TSE_DIM", QMetaType.Type.QString),
        ],
    },
    
    "Va": {
        "fields": [
            ("fid", QMetaType.Type.Int),
            ("UUID", QMetaType.Type.QString),
            ("VA_ESS", QMetaType.Type.QString),
            ("VA_TX_HA", QMetaType.Type.Double),
            ("VA_CUMUL_TX_VA", QMetaType.Type.Double),
        ],
    },
    
    "Reg": {
        "fields": [
            ("fid", QMetaType.Type.Int),
            ("UUID", QMetaType.Type.QString),
            ("REG_ESS", QMetaType.Type.QString),
            ("REG_STADE", QMetaType.Type.QString),
            ("REG_ETAT", QMetaType.Type.QString),
        ],
    },
}