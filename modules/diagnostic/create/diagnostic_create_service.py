import processing

from qgis.core import (
    QgsProject,
    QgsProcessing,
    QgsMapLayer,
    QgsWkbTypes
)
from qgis.utils import iface

from ....core.layer.factory import LayerFactory
from ....core.db.manager import DatabaseManager

from ....utils.layers import load_gpkg, create_relation, set_relation_label, load_vectors
from ....utils.utils import fold, unfold

from ..layer_schema import DIAGNOSTIC_LAYERS

# configurators
from ..configurators.placette import PlacetteConfigurator
from ..configurators.transect import TransectConfigurator
from ..configurators.limite import LimiteConfigurator
from ..configurators.picto import PictoConfigurator
from ..configurators.gha import GhaConfigurator
from ..configurators.tse import TseConfigurator
from ..configurators.va import VaConfigurator
from ..configurators.reg import RegConfigurator

class DiagnosticCreateService:
    def __init__(
        self,
        dendro_controller,
        grid_controller,
        raster_controller
    ):

        self.iface = iface
        self.project = QgsProject.instance()

        self.dendro = dendro_controller.get_values()

        self.grid_controller = grid_controller
        self.raster_controller = raster_controller

    def run(self):
        
        print("_create_layers")
        layers = self._create_layers()
        print("_package_layers")
        gpkg_path = self._package_layers(layers)

        layers = load_gpkg(gpkg_path, group_name="DIAGNOSTIC")

        relations = self._create_relations(layers)
        
        self._configure_layers(layers, relations)

        vector_layers = load_vectors('ua_polygon', 'infra_point', 'infra_line', 'infra_polygon', 'route_line', group_name="VECTEUR")
        self._configure_flags(layers, vector_layers)
        
        self._save_style(layers)

        self.raster_controller.load_selected_rasters()

        fold()
        unfold("DIAGNOSTIC")

        return gpkg_path

    def _create_layers(self):

        layers = LayerFactory.create_all(DIAGNOSTIC_LAYERS)

        layers["Essences"] = DatabaseManager().load_essences("Essences")
        self.essences = layers["Essences"]

        if self.grid_controller.is_valid():
            layers["Grid"] = self.grid_controller.create_grid()

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

        PlacetteConfigurator(placette, relations).configure()
        TransectConfigurator(transect, self.dendro, essences).configure()
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

        print("set_relation_label")
        for name, label in relation_labels.items():
            set_relation_label(placette, relations[name], label)

    def _configure_flags(self, layers, vector_layers):

        for layer in layers.values():
            if layer.geometryType() == QgsWkbTypes.NullGeometry:

                flags = layer.flags()
                flags |= QgsMapLayer.Private
                layer.setFlags(flags)

        for layer in vector_layers:
            flags = layer.flags()
            flags &= ~QgsMapLayer.Searchable     # non recherchable
            flags &= ~QgsMapLayer.Identifiable   # non cliquable avec l'outil Identifier
            layer.setFlags(flags)
            layer.setReadOnly(True)

    def _save_style(self, layers):

        for layer in layers.values():

            layer.saveStyleToDatabase(
                name="default",
                description="default",
                useAsDefault=True,
                uiFileContent=""
            )
