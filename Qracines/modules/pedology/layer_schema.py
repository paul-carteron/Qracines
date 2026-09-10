from qgis.PyQt.QtCore import QMetaType


PEDOLOGY_LAYERS = {
    "sondage": {
        "geometry": "Point",
        "fields": [
            ("fid", QMetaType.Type.Int),
            ("uuid", QMetaType.Type.QString),
            ("rmq", QMetaType.Type.QString),
            ("humus", QMetaType.Type.QString),
            ("topographie", QMetaType.Type.QString),
            ("exposition", QMetaType.Type.QString),
            ("station", QMetaType.Type.QString),
            ("arret", QMetaType.Type.QString),
            ("photo", QMetaType.Type.QString),
        ],
    },
    "horizons": {
        "fields": [
            ("fid", QMetaType.Type.Int),
            ("sondage", QMetaType.Type.QString),
            ("type", QMetaType.Type.QString),
            ("epaisseur", QMetaType.Type.Int),
            ("humidite", QMetaType.Type.QString),
            ("texture", QMetaType.Type.QString),
            ("couleur", QMetaType.Type.QString),
            ("structure", QMetaType.Type.QString),
            ("compacite", QMetaType.Type.QString),
            ("eg", QMetaType.Type.Bool),
            ("eg_taille", QMetaType.Type.QString),
            ("eg_proportion", QMetaType.Type.Double),
            ("hm", QMetaType.Type.Bool),
            ("hm_tache", QMetaType.Type.QString),
            ("hm_proportion", QMetaType.Type.Double),
            ("car", QMetaType.Type.Bool),
            ("car_localisation", QMetaType.Type.QString),
            ("car_puissance", QMetaType.Type.QString),
            ("profondeur", QMetaType.Type.Int),
        ],
    },
}
