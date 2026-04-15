import processing

from qgis.core import QgsWkbTypes, QgsMapLayer

# Import from utils folder
from ....utils.layers import load_gpkg, create_relation, set_relation_label
from ....utils.config import get_qfield_path

# configurators
from ..configurators.placette import PlacetteConfigurator
from ..configurators.transect import TransectConfigurator
from ..configurators.limite import LimiteConfigurator
from ..configurators.gha import GhaConfigurator
from ..configurators.tse import TseConfigurator
from ..configurators.va import VaConfigurator
from ..configurators.reg import RegConfigurator

class ExpertiseLoad:
    def __init__(self):
        self.gpkg_path = get_qfield_path("expertise_gpkg")
    
    def load(self):

        layers = load_gpkg(self.gpkg_path, group_name="EXPERTISE")
        relations = self._create_relations(layers)
        self._configure_layers(layers, relations)

        return layers

    def _create_relations(self, layers):

        relations = {
            "gha": create_relation(layers["placette"], layers["gha"], "UUID", "UUID"),
            "tse": create_relation(layers["placette"], layers["tse"], "UUID", "UUID"),
            "va":  create_relation(layers["placette"], layers["va"], "UUID", "UUID"),
            "reg": create_relation(layers["placette"], layers["reg"], "UUID", "UUID"),
        }

        return relations

    def _configure_layers(self, layers, relations):
        essences = layers["essences"]
        placette = layers["placette"]
        transect = layers["transect"]
        limite = layers["limite"]
        gha = layers["gha"]
        tse = layers["tse"]
        va = layers["va"]
        reg = layers["reg"]

        dendro = {
          "dmin": 0,
          "dmax": 200,
          "hmin": 0,
          "hmax": 50,
        }

        codes = ["CHE", "HET", "EPC", "DOU"]
        codes_taillis = ["BOU", "CHA", "CHE", "ECH", "FRE", "HET", "NOI", "SAU", "TIL", "TRE"]

        PlacetteConfigurator(placette, relations).configure()
        TransectConfigurator(transect, dendro, essences, codes).configure()
        LimiteConfigurator(limite).configure()
        GhaConfigurator(gha, essences, codes).configure()
        TseConfigurator(tse, essences, codes_taillis).configure()
        VaConfigurator(va, essences, codes).configure()
        RegConfigurator(reg, essences, codes).configure()

        relation_labels = {
            "gha": "Surface terrière",
            "tse": "Essence taillis",
            "va": "Valeur avenir",
            "reg": "Régénération",
        }

        for name, label in relation_labels.items():
            relation = relations[name]
            set_relation_label(placette, relation, label)