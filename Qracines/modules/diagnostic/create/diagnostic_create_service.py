import processing

from qgis.core import QgsProject, Qgis, QgsProcessing, QgsMapLayer, QgsWkbTypes
from qgis.utils import iface

from ....core.layer.factory import LayerFactory
from ....core.db.manager import DatabaseManager

from ....utils.layers import load_gpkg, create_relation, set_relation_label
from ....utils.utils import fold, unfold
from ....utils.variable import get_global_variable
from ....utils.essence import load_essences

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

from qsequoia2.modules.utils.seq_config import seq_read

class DiagnosticCreateService:
    def __init__(
        self,
        seq_dir,
        dendro_controller,
        grid_controller,
        raster_controller
    ):

        self.iface = iface
        self.project = QgsProject.instance()

        self.seq_dir = seq_dir

        self.dendro = dendro_controller.get_values()

        self.grid_controller = grid_controller
        self.raster_controller = raster_controller

    def run(self):
        
        layers = self._create_layers()
        gpkg_path = self._package_layers(layers)

        layers = load_gpkg(gpkg_path, group_name="DIAGNOSTIC")

        relations = self._create_relations(layers)
        
        self._configure_layers(layers, relations)
        
        vkeys = [
            'v.seq.ua.poly',
            'v.infra.point', 'v.infra.line', 'v.infra.poly',
            'v.vege.line',
            'v.hydro.point', 'v.hydro.line', 'v.hydro.poly',
            'v.road.line'
        ]

        for key in vkeys:
            try:
                style_dir = get_global_variable("QS2_styles_directory")
                vlayers = seq_read(key, seq_dir=self.seq_dir, add_to_project=True, style_folder=style_dir)
            except Exception as e:
                continue

        # if vlayers:
        #     self._configure_flags(layers, vlayers)

        try:
            self.raster_controller.load_selected_rasters(self.seq_dir)

        except Exception as e:
            iface.messageBar().pushMessage("Erreur", str(e), level=Qgis.Info, duration=5)

        fold()
        unfold("DIAGNOSTIC")

        return gpkg_path

    def _create_layers(self):

        layers = LayerFactory.create_all(DIAGNOSTIC_LAYERS)

        layers["Essences"] = load_essences(name = "Essences")
        self.essences = layers["Essences"]

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

