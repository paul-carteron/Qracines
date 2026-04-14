import processing

from qgis.core import QgsProject, QgsProcessing, QgsMapLayer, QgsField, QgsFeature
from qgis.PyQt.QtCore import QVariant

from ....core.layer.factory import LayerFactory
from ....core.db.manager import DatabaseManager

from ....utils.layers import load_gpkg
from ....utils.utils import fold, unfold

from ..layer_schema import TREE_MARKING_LAYERS

from ..configurators.param import ParamConfigurator
from ..configurators.arbres import ArbresConfigurator

_SKIP_VARIATIONS = {"foudroyé", "nécrosé", "dépérissant"}

class TreeMarkingCreateService:

    def __init__(
        self,
        forest_id: str,
        codes: list,
        dendro_controller,
        raster_controller
    ):

        self.project = QgsProject.instance()

        self.forest_id = forest_id
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
        lst_hauteur = layers["lst_hauteur"]
        lst_diam = layers["lst_diam"]

        ParamConfigurator(param, self.forest_id).configure()
        ArbresConfigurator(arbres, param, essences, lst_hauteur, lst_diam).configure()

        # Make layer private
        lst_hauteur.setFlags(lst_hauteur.flags() | QgsMapLayer.Private)
        lst_diam.setFlags(lst_diam.flags() | QgsMapLayer.Private)

        essences.setDisplayExpression('''CASE WHEN "selected" THEN '✅ ' ELSE '❌ ' END || "essence_variation"''')
        param.setDisplayExpression('"PARCELLE" || "SURFACE"')

        self._save_style(layers)

        self.raster_controller.load_selected_rasters()

        fold()
        unfold("INVENTAIRE")

        return gpkg_path

    def _create_layers(self):

        layers = LayerFactory.create_all(TREE_MARKING_LAYERS)

        essences = DatabaseManager().load_essences("Essences")
        layers["Essences"] = essences

        self.project.addMapLayers(list(layers.values()), addToLegend=False)

        self._init_essences(essences)
        self._init_range_layer(layers["lst_hauteur"], 0, 50)
        self._init_range_layer(layers["lst_diam"], 5, 150, 5)

        return layers
    
    def _init_essences(self, layer):

        # ajouter champ si absent
        if layer.fields().indexOf("selected") == -1:
            layer.dataProvider().addAttributes([QgsField("selected", QVariant.Bool)])
            layer.updateFields()

        if not layer.isEditable():
            layer.startEditing()

        selected_idx = layer.fields().indexOf("selected")
        for f in layer.getFeatures():
            if f['variation'] in _SKIP_VARIATIONS:
                continue

            value = f['code'] in self.codes
            layer.changeAttributeValue(f.id(), selected_idx, value)

        layer.commitChanges()

    def _init_range_layer(self, layer, min_val, max_val, step=1):
        if not layer.isEditable():
            layer.startEditing()

        provider = layer.dataProvider()

        provider.deleteFeatures([f.id() for f in layer.getFeatures()])

        feats = []
        for v in range(min_val, max_val + 1, step):
            f = QgsFeature(layer.fields())
            f["VALEUR"] = v
            feats.append(f)

        provider.addFeatures(feats)
        layer.commitChanges()

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