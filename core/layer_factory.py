# layer_factory.py

from pathlib import Path
from qgis.PyQt.QtCore import QVariant
from ..utils.qfield_utils import create_memory_layer

class LayerFactory:
    """Create any of the plugin’s in-memory layers by name."""

    # 1️⃣  Define each layer’s schema in one place:
    LAYERS = {
        # DIAGNOSTIC
        "Placette": {
            "fields": [
                # Peuplement
                ("PLACETTE", QVariant.String),
                ("PLTM_PARC", QVariant.String),
                ("PLTM_TYPE", QVariant.String),
                ("PLTM_RICH", QVariant.String),
                ("PLTM_STADE", QVariant.String),
                ("PLTM_PB", QVariant.String), 
                ("PLTM_SANT", QVariant.String), 
                ("PLTM_MEC", QVariant.String),
                ("PLTM_HISTO", QVariant.String), 
                ("PLTM_AME", QVariant.String), 
                ("PLTM_RMQ", QVariant.String), 
                ("PICTURES", QVariant.String),
                # Taillis
                ("TSE_DENS", QVariant.String),
                ("TSE_VOL", QVariant.Double),
                ("TSE_NATURE", QVariant.String),
                ("TSE_POTEN", QVariant.String),
                ("TSE_CLOISO", QVariant.String),
                ("TSE_RMQ", QVariant.String),
                # Valeur avenir
                ("VA_REG", QVariant.String),
                ("VA_TX_TROUEE", QVariant.Double),
                ("VA_NHA", QVariant.Double),
                ("VA_VEG_CO", QVariant.String),
                ("VA_TX_DEG", QVariant.Double),
                ("VA_DEG", QVariant.String),
                ("VA_RMQ", QVariant.String),
        ],
            "geometry": "Point"
        },
        "Transect": {
            "fields": [
            ("UUID", QVariant.String),
            ("PLTM_PARC", QVariant.String),
            ("PLTM_GROUPE", QVariant.String),
            ("TR_TYPE_ESS", QVariant.String),
            ("TR_ESS",  QVariant.LongLong),
            ("TR_DIAM", QVariant.Int),
            ("TR_EFFECTIF", QVariant.Int),
            ("TR_HAUTEUR", QVariant.Int)
            ],
            "geometry": "Point"
        },
        "Limite": {
            "fields": [
                ("TYPE", QVariant.String), 
                ("RMQ", QVariant.String)
            ],
            "geometry": "LineString"
        },
        "Picto": {
            "fields": [
            ("TYPE", QVariant.String),
            ("NATURE", QVariant.String),
            ("PICTURES", QVariant.String)
            ],
            "geometry": "Point"
        },
        "Gha": {
            "fields": [
            ("RES_ESS", QVariant.String),
            ("RES_G", QVariant.Int),
            ("PLACETTE", QVariant.String)
            ],
        },
        "Tse": {
            "fields": [
            ("TSE_ESS", QVariant.String),
            ("TSE_DM", QVariant.String),
            ("PLACETTE", QVariant.String)
            ],
        },
        "Reg": {
            "fields": [
            ("REG_ESS", QVariant.String),
            ("REG_STADE", QVariant.String),
            ("REG_ETAT", QVariant.String),
            ("PLACETTE", QVariant.String)
            ],
        },
        "Va_ess": {
            "fields": [
            ("PLACETTE", QVariant.String),
            ("VA_ESS", QVariant.String),
            ("VA_STADE", QVariant.String),
            ("VA_AGE_APP", QVariant.Int),
            ("VA_HT", QVariant.Double),
            ("VA_ELAG", QVariant.String),
            ("VA_TX_HA", QVariant.Double),
            ("CUMUL_TX_VA", QVariant.Double)
            ],
        },
        # INVENTAIRE
        "arbres": {
            "fields": [
            ("fid", QVariant.Int),
            ("ID_CODE", QVariant.String),
            ("UUID", QVariant.String),
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
            "geometry": "Point"
        },
        # PEDOLOGY
        "sondage": {
            "fields": [
                ("fid", QVariant.Int),
                ("uuid", QVariant.String),
                ("humus", QVariant.String),
                ("topographie", QVariant.String),
                ("exposition", QVariant.String),
                ("station", QVariant.String),
                ("arret", QVariant.String),
                ("photo", QVariant.String)
            ],
            "geometry": "Point"
        },
        "horizons": {
            "fields": [
                ("fid", QVariant.Int),
                ("sondage", QVariant.String),
                ("type", QVariant.String),
                ("epaisseur", QVariant.String),
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
                ("profondeur", QVariant.String)
            ]
        }
    }

    @classmethod
    def create(cls, name: str):
        """Return a new memory layer for the given name."""
        cfg = cls.LAYERS.get(name)
        if cfg is None:
            raise ValueError(f"Unknown layer type: {name}")
        return create_memory_layer(name, cfg["fields"], cfg.get("geometry"))
