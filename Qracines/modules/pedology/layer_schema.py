from qgis.PyQt.QtCore import QMetaType


PEDOLOGY_LAYERS = {
    "sondage": {
        "geometry": "Point",
        "fields": [
            ("UUID", QMetaType.Type.QString),
            ("GUIDE", QMetaType.Type.QString),
            ("REMARQUE", QMetaType.Type.QString),
            ("HUMUS", QMetaType.Type.QString),
            ("TOPOGRAPHIE", QMetaType.Type.QString),
            ("EXPOSITION", QMetaType.Type.QString),
            ("STATION", QMetaType.Type.QString),
            ("ARRET", QMetaType.Type.QString),
            ("PHOTO", QMetaType.Type.QString),
        ],
    },
    "horizons": {
        "fields": [
            ("SONDAGE", QMetaType.Type.QString),
            ("TYPE", QMetaType.Type.QString),
            ("EPAISSEUR", QMetaType.Type.Int),
            ("HUMIDITE", QMetaType.Type.QString),
            ("TEXTURE", QMetaType.Type.QString),
            ("COULEUR", QMetaType.Type.QString),
            ("STRUCTURE", QMetaType.Type.QString),
            ("COMPACITE", QMetaType.Type.QString),
            ("EG", QMetaType.Type.Bool),
            ("EG_TAILLE", QMetaType.Type.QString),
            ("EG_PROPORTION", QMetaType.Type.Double),
            ("HM", QMetaType.Type.Bool),
            ("HM_TACHE", QMetaType.Type.QString),
            ("HM_PROPORTION", QMetaType.Type.Double),
            ("CAR", QMetaType.Type.Bool),
            ("CAR_LOCALISATION", QMetaType.Type.QString),
            ("CAR_PUISSANCE", QMetaType.Type.QString)
        ],
    },
}
