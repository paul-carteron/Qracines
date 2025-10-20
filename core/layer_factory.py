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
                    # placette
                    ("fid", QVariant.Int),
                    ("UUID", QVariant.String),
                    ("COMPTEUR", QVariant.LongLong),
                    ("PLT_PARCELLE", QVariant.String),
                    ("PLT_TYPE", QVariant.String),
                    ("PLT_RICH", QVariant.String),
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
                "geometry": "Point"
            },
            "Transect": {
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
                "geometry": "Point"
            },
            "Limite": {
                "fields": [
                    ("fid", QVariant.Int),
                    ("UUID", QVariant.String),
                    ("LINE_TYPE", QVariant.String), 
                    ("LINE_RMQ", QVariant.String), 
                    ("LINE_PHOTO", QVariant.String)
                ],
                "geometry": "LineString"
            },
            "Picto": {
                "fields": [
                    ("fid", QVariant.Int),
                    ("UUID", QVariant.String),
                    ("POINT_TYPE", QVariant.String),
                    ("POINT_RMQ", QVariant.String), 
                    ("POINT_PHOTO", QVariant.String)
                ],
                "geometry": "Point"
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
        },
        "INVENTAIRE": {
            "arbres": {
                "fields": [
                ("fid", QVariant.Int),
                ("ID_CODE", QVariant.String),
                ("UUID", QVariant.String),
                ("LOT", QVariant.String),
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
                    ("rmq", QVariant.String),
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
        },
        "EXPERTISE": {
            "placette": {
                "fields": [
                    ("fid", QVariant.Int),
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
            "limite": {
                "fields": [
                    ("fid", QVariant.Int),
                    ("LIMITE_TYPE", QVariant.String), 
                    ("LIMITE_RMQ", QVariant.String)
                ],
                "geometry": "LineString"
            },
            "gha": {
                "fields": [
                    ("fid", QVariant.Int),
                    ("UUID", QVariant.String),
                    ("GHA_ESSENCE_ID", QVariant.String),
                    ("GHA_ESSENCE_SECONDAIRE_ID", QVariant.String),
                    ("GHA_G", QVariant.Int),
                ],
            },
            "tse": {
                "fields": [
                    ("fid", QVariant.Int),
                    ("UUID", QVariant.String),
                    ("TSE_ESSENCE_ID", QVariant.String),
                    ("TSE_ESSENCE_SECONDAIRE_ID", QVariant.String),
                ],
            },
            "va": {
                "fields": [
                    ("fid", QVariant.Int),
                    ("UUID", QVariant.String),
                    ("VA_ESSENCE_ID", QVariant.String),
                    ("VA_ESSENCE_SECONDAIRE_ID", QVariant.String),
                    ("VA_AGE_APP", QVariant.LongLong),
                    ("VA_TX_TROUEE", QVariant.LongLong),
                    ("VA_TX_HA", QVariant.Double),
                    ("CUMUL_TX_VA", QVariant.Double)
                ],
            },
            "reg": {
                "fields": [
                    ("fid", QVariant.Int),
                    ("UUID", QVariant.String),
                    ("REG_ESSENCE_ID", QVariant.String),
                    ("REG_ESSENCE_SECONDAIRE_ID", QVariant.String),
                    ("REG_STADE", QVariant.String),
                    ("REG_ETAT", QVariant.String),
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

    @classmethod
    def get_layer_names(cls, category: str):
        """Return a list of layer names for the given category."""
        category_config = cls.LAYERS.get(category)
        if category_config is None:
            raise ValueError(f"Unknown category: {category!r}")
        
        return list(category_config.keys())

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
