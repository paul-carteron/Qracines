from qgis.PyQt.QtCore import QVariant

PEDOLOGY_LAYERS = {

    "sondage": {
        "geometry": "Point",
        "fields": [
            ("fid", QVariant.Int),
            ("uuid", QVariant.String),
            ("rmq", QVariant.String),
            ("humus", QVariant.String),
            ("topographie", QVariant.String),
            ("exposition", QVariant.String),
            ("station", QVariant.String),
            ("arret", QVariant.String),
            ("photo", QVariant.String)
        ],

    },

    "horizons": {
        "fields": [
            ("fid", QVariant.Int),
            ("sondage", QVariant.String),
            ("type", QVariant.String),
            ("epaisseur", QVariant.Int),
            ("humidite", QVariant.String),
            ("texture", QVariant.String),
            ("couleur", QVariant.String),
            ("structure", QVariant.String),
            ("compacite", QVariant.String),
            ("eg", QVariant.Bool),
            ("eg_taille", QVariant.String),
            ("eg_proportion", QVariant.Double),
            ("hm", QVariant.Bool),
            ("hm_tache", QVariant.String),
            ("hm_proportion", QVariant.Double),
            ("car", QVariant.Bool),
            ("car_localisation", QVariant.String),
            ("car_puissance", QVariant.String),
            ("profondeur", QVariant.Int)
        ]
    },
    }