# Import from utils folder
from ....utils.layers import load_gpkg, create_relation, set_relation_label
from ....utils.config import get_qfield_path

# configurators
from ..configurators.placette import PlacetteConfigurator
from ..configurators.transect import TransectConfigurator
from ..configurators.limite import LimiteConfigurator
from ..configurators.picto import PictoConfigurator
from ..configurators.gha import GhaConfigurator
from ..configurators.tse import TseConfigurator
from ..configurators.va import VaConfigurator
from ..configurators.reg import RegConfigurator

class DiagnosticLoad:
    def __init__(self):
        self.gpkg_path = get_qfield_path("diag")
    
    def load(self):

        layers = load_gpkg(self.gpkg_path, group_name="DIAGNOSTIC")
        relations = self._create_relations(layers)
        self._configure_layers(layers, relations)

        return layers
    def _create_relations(self, layers):
        
        relations = {
            "Gha": create_relation(layers["Placette"], layers["Gha"], "UUID", "UUID"),
            "Tse": create_relation(layers["Placette"], layers["Tse"], "UUID", "UUID"),
            "Va":  create_relation(layers["Placette"], layers["Va"], "UUID", "UUID"),
            "Reg": create_relation(layers["Placette"], layers["Reg"], "UUID", "UUID"),
        }

        return relations
    
    def _configure_layers(self, layers, relations):
        essences = layers["Essences"]
        placette = layers["Placette"]
        transect = layers["Transect"]
        limite = layers["Limite"]
        picto = layers["Picto"]
        gha = layers["Gha"]
        tse = layers["Tse"]
        va = layers["Va"]
        reg = layers["Reg"]

        dendro = {
          "dmin": 0,
          "dmax": 200,
          "hmin": 0,
          "hmax": 50,
        }

        PlacetteConfigurator(placette, relations).configure()
        TransectConfigurator(transect, dendro, essences).configure()
        LimiteConfigurator(limite).configure()
        PictoConfigurator(picto).configure()
        GhaConfigurator(gha, essences).configure()
        TseConfigurator(tse, essences).configure()
        VaConfigurator(va, essences).configure()
        RegConfigurator(reg, essences).configure()

        relation_labels = {
            "Gha": "Surface terrière",
            "Tse": "Essence taillis",
            "Va": "Valeur avenir",
            "Reg": "Régénération",
        }

        for name, label in relation_labels.items():
            set_relation_label(placette, relations[name], label)

