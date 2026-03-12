import processing

from qgis.core import QgsProject, QgsProcessing, QgsMapLayer

from ....core.layer.factory import LayerFactory
from ....core.db.manager import DatabaseManager

from ....utils.layers import load_gpkg
from ....utils.utils import fold, unfold

from ..layer_schema import TREE_MARKING_LAYERS

from ..configurators.param import ParamConfigurator
from ..configurators.arbres import ArbresConfigurator

class TreeMarkingService:

    def __init__(
        self,
        codes: list,
        dendro_controller,
        raster_controller
    ):

        self.project = QgsProject.instance()

        self.codes = codes
        self.dendro = dendro_controller.get_values()

        self.raster_controller = raster_controller

    def run(self):

        layers = self._create_layers()
        gpkg_path = self._package_layers(layers)

        layers = load_gpkg(gpkg_path, group_name="INVENTAIRE")

        param = layers["Param"]
        arbres = layers["Arbres"]
        essences = layers["Essences"]

        ParamConfigurator(param).configure()
        ArbresConfigurator(arbres, param, self.dendro, essences, self.codes).configure()

        # Make essence layer private
        essences.setFlags(essences.flags() | QgsMapLayer.Private)

        self._save_style(layers)

        self.raster_controller.load_selected_rasters()

        fold()
        unfold("INVENTAIRE")

        return gpkg_path

    def _create_layers(self):

        layers = LayerFactory.create_all(TREE_MARKING_LAYERS)

        layers["Essences"] = DatabaseManager().load_essences("Essences")

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

    def _save_style(self, layers):

        for layer in layers.values():

            layer.saveStyleToDatabase(
                name="default",
                description="default",
                useAsDefault=True,
                uiFileContent=""
            )