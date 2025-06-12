from qgis.PyQt.QtCore import QVariant

from qgis.core import (
    QgsVectorLayer,
    QgsFields,
    QgsField,
    QgsCoordinateReferenceSystem,
)

class LayerFactory:
    """Create any of the plugin’s in-memory layers by name."""

    # 1️⃣  Define each layer’s schema in one place:
    LAYERS = {
        "DIAGNOSTIC": {
            "Placette": {
                "fields": [
                    # Peuplement
                    ("PLACETTE", QVariant.String),
                    ("PLTM_PARC", QVariant.String),
                    ("PLTM_STRATE", QVariant.String),
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
        },
        "INVENTAIRE": {
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
         },
        "PEDOLOGY": {
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
            },
        },
        "EXPERTISE": {
            "placette": {
                "fields": [
                    ("fid", QVariant.Int),
                    ("UUID", QVariant.String),
                    # Peuplement
                    ("PLTM_PARCELLE", QVariant.String),
                    ("PLTM_STRATE", QVariant.String),
                    ("PLTM_TYPE", QVariant.String),
                    # Valeur avenir
                    ("VA_TX_TROUEE", QVariant.LongLong),
            ],
                "geometry": "Point"
            },
            "transect": {
                "fields": [
                ("fid", QVariant.Int),
                ("UUID", QVariant.String),
                ("TR_PARCELLE", QVariant.String),
                ("TR_STRATE", QVariant.String),
                ("TR_ESSENCE_ID", QVariant.String),
                ("TR_ESSENCE_SECONDAIRE_ID", QVariant.String),
                ("TR_DIAMETRE", QVariant.String),
                ("TR_EFFECTIF", QVariant.LongLong),
                ("TR_HAUTEUR", QVariant.String),
                ],
                "geometry": "Point"
            },
            "gha": {
                "fields": [
                ("UUID", QVariant.String),
                ("RES_ESS", QVariant.String),
                ("RES_G", QVariant.Int),
                ],
            },
            "tse": {
                "fields": [
                ("UUID", QVariant.String),
                ("TSE_ESS", QVariant.String),
                ("TSE_DM", QVariant.String),
                ],
            },
            "reg": {
                "fields": [
                ("UUID", QVariant.String),
                ("REG_ESS", QVariant.String),
                ("REG_STADE", QVariant.String),
                ("REG_ETAT", QVariant.String),
                ],
            },
            "va_ess": {
                "fields": [
                ("UUID", QVariant.String),
                ("VA_ESS", QVariant.String),
                ("VA_AGE_APP", QVariant.Int),
                ("VA_TX_HA", QVariant.Double),
                ("CUMUL_TX_VA", QVariant.Double)
                ],
            },
        },
    }

    @classmethod
    def create(cls, name: str, category: str):
        """Return a new memory layer for the given name."""
        category_config = cls.LAYERS.get(category)
        if category_config is None:
            raise ValueError(f"Unknown category: {category!r}")
        
        layer_config = category_config.get(name)
        if layer_config is None:
            raise ValueError(f"Unknown layer '{name}' in category '{category}'")
        
        return cls.create_memory_layer(name, layer_config.get("fields"), layer_config.get("geometry"))

    @staticmethod
    def create_memory_layer(layer_name, fields_list, geometry = None, crs = "EPSG:2154"):

        if geometry:
            crs_obj = QgsCoordinateReferenceSystem(crs)
            geometry_str = f"{geometry}?crs={crs_obj.authid()}"
        else:
            geometry_str = "None"

        # Create the layer
        layer = QgsVectorLayer(geometry_str, layer_name, "memory")
        if not layer.isValid():
            print("Failed to create the layer!")
            return False

        # Add fields to the layer
        fields = QgsFields()
        for field_name, field_type in fields_list:
            fields.append(QgsField(field_name, field_type))
        layer.dataProvider().addAttributes(fields)
        layer.updateFields()

        return layer
