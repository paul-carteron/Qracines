import processing

from qgis.core import QgsProcessing, QgsProject

from ....core.layer.factory import LayerFactory
from ....utils.config import get_stations, get_style
from ....utils.layers import create_relation, load_gpkg
from ....utils.message import messageLog
from ....utils.utils import fold, unfold
from ..configurators.sondage import SondageConfigurator
from ..layer_schema import PEDOLOGY_LAYERS

from qsequoia2.modules.utils.seq_config import seq_read


class PedologyCreateService:
    def __init__(
        self,
        guide: str,
        seq_dir,
        style_dir,
        seq_vect_keys: list,
        seq_rast_keys: list,
    ):
        self.project = QgsProject.instance()
        self.guide = guide
        self.seq_dir = seq_dir
        self.style_dir = style_dir
        self.seq_vect_keys = seq_vect_keys
        self.seq_rast_keys = seq_rast_keys

    def run(self):
        layers = self._create_layers()
        gpkg_path = self._package_layers(layers)

        layers = load_gpkg(gpkg_path, group_name="PEDOLOGY")
        self._create_relation(layers)
        self._configure_layers(layers)

        for key in (self.seq_vect_keys + self.seq_rast_keys):
            try:
                seq_read(key, self.seq_dir, add_to_project=True, style_folder=self.style_dir)
            except Exception as e:
                messageLog(f"Could not load layer {key}: {e}")

        fold()
        unfold("PEDOLOGY")

        return gpkg_path

    def _create_layers(self):
        layers = LayerFactory.create_all(PEDOLOGY_LAYERS)
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

        for layer in layers.values():
            self.project.removeMapLayer(layer.id())

        return result["OUTPUT"]

    def _create_relation(self, layers):
        return create_relation(
            layers["sondage"], layers["horizons"],
            "uuid", "sondage",
            relation_id="sondage_horizons", relation_name="sondage",
        )

    def _configure_layers(self, layers):
        stations = get_stations(self.guide)
        SondageConfigurator(layers["sondage"], stations).configure()
