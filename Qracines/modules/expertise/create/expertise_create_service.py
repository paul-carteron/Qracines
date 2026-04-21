import processing

from qgis.core import Qgis, QgsProject, QgsProcessing, QgsWkbTypes, QgsMapLayer
from qgis.utils import iface

from ....core.layer.factory import LayerFactory
from ....core.db.manager import DatabaseManager

from ....utils.layers import load_gpkg, create_relation, set_relation_label
from ....utils.utils import fold, unfold
from ....utils.essence import load_essences
from ..layer_schema import EXPERTISE_LAYERS

# configurators
from ..configurators.placette import PlacetteConfigurator
from ..configurators.transect import TransectConfigurator
from ..configurators.limite import LimiteConfigurator
from ..configurators.gha import GhaConfigurator
from ..configurators.tse import TseConfigurator
from ..configurators.va import VaConfigurator
from ..configurators.reg import RegConfigurator

class ExpertiseCreateService:

    def __init__(
        self,
        seq_dir,
        codes: list,
        codes_taillis: list,
        dendro_controller,
        grid_controller,
        raster_controller
    ):

        self.iface = iface
        self.project = QgsProject.instance()

        self.seq_dir = seq_dir

        self.codes = codes
        self.codes_taillis = codes_taillis
        self.dendro = dendro_controller.get_values()

        self.grid_controller = grid_controller
        self.raster_controller = raster_controller

    def run(self):
        
        layers = self._create_layers()
        gpkg_path = self._package_layers(layers)

        layers = load_gpkg(gpkg_path, group_name="EXPERTISE")

        relations = self._create_relations(layers)

        self._configure_layers(layers, relations)
        self._configure_flags(layers)

        try:
            self.raster_controller.load_selected_rasters(self.seq_dir)
        except Exception as e:
            iface.messageBar().pushMessage("Erreur", str(e), level=Qgis.Info, duration=5)

        fold()
        unfold("EXPERTISE")

        return gpkg_path

    def _create_layers(self):

        layers = LayerFactory.create_all(EXPERTISE_LAYERS)

        layers["essences"] = load_essences(name = "essences")

        if self.grid_controller.is_valid():
            layers["Grid"] = self.grid_controller.create_grid(self.seq_dir)

        self.project.addMapLayers(list(layers.values()), addToLegend=False)

        return layers
    
    def _package_layers(self, layers, outpath=QgsProcessing.TEMPORARY_OUTPUT):

        result = processing.run(
            "native:package",
            {
                "LAYERS": list(layers.values()),
                "OUTPUT": outpath,
                "OVERWRITE": True,
                "SAVE_STYLES": True,
                "EXPORT_RELATED_LAYERS": True,
            },
        )

        gpkg_path = result["OUTPUT"]

        # remove temporary layers
        for layer in layers.values():
            self.project.removeMapLayer(layer.id())

        return gpkg_path

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

        PlacetteConfigurator(placette, relations).configure()
        TransectConfigurator(transect, self.dendro, essences, self.codes).configure()
        LimiteConfigurator(limite).configure()
        GhaConfigurator(gha, essences, self.codes).configure()
        TseConfigurator(tse, essences,self.codes_taillis).configure()
        VaConfigurator(va, essences,self.codes).configure()
        RegConfigurator(reg, essences, self.codes).configure()

        relation_labels = {
            "gha": "Surface terrière",
            "tse": "Essence taillis",
            "va": "Valeur avenir",
            "reg": "Régénération",
        }

        for name, label in relation_labels.items():
            relation = relations[name]
            set_relation_label(placette, relation, label)

    def _configure_flags(self, layers):

        for layer in layers.values():

            if layer.geometryType() == QgsWkbTypes.NullGeometry:

                flags = layer.flags()
                flags |= QgsMapLayer.Private
                layer.setFlags(flags)