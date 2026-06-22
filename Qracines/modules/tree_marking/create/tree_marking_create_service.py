import processing

from Qracines.utils.message import messageLog

from qgis.core import QgsProject, QgsProcessing, QgsMapLayer, QgsField, QgsFeature
from qgis.PyQt.QtCore import QVariant

from ....core.layer.factory import LayerFactory

from ....utils.layers import load_gpkg
from ....utils.utils import fold, unfold
from ....utils.essence import load_essences
from ..layer_schema import TREE_MARKING_LAYERS

from ..configurators.lot import LotConfigurator
from ..configurators.arbres import ArbresConfigurator
from ..configurators.param import ParamConfigurator
from ..configurators.essences import EssencesConfigurator

from qsequoia2.modules.utils.seq_config import seq_read

_SKIP_VARIATIONS = {"foudroyé", "nécrosé", "dépérissant"}

class TreeMarkingCreateService:

    def __init__(
        self,
        seq_id: str,
        seq_dir,
        style_dir,
        codes: list,
        dendro_controller,
        seq_vect_keys: list,
        seq_rast_keys: list,
    ):

        self.project = QgsProject.instance()

        self.seq_id = seq_id
        self.seq_dir = seq_dir
        self.style_dir = style_dir

        self.codes = codes
        self.dendro = dendro_controller.get_values()

        self.seq_vect_keys = seq_vect_keys
        self.seq_rast_keys = seq_rast_keys

    def run(self):

        layers = self._create_layers()
        gpkg_path = self._package_layers(layers)

        layers = load_gpkg(gpkg_path, group_name="INVENTAIRE")

        param = layers["Param"]
        lot = layers["Lot"]
        arbres = layers["Arbres"]
        essences = layers["Essences"]
        lst_hauteur = layers["lst_hauteur"]
        lst_diam = layers["lst_diam"]

        ParamConfigurator(param).configure()
        LotConfigurator(lot, seq_id=self.seq_id).configure()
        ArbresConfigurator(arbres, lot, essences, lst_hauteur, lst_diam).configure()
        EssencesConfigurator(essences).configure()

        # Make layer private
        lst_hauteur.setFlags(lst_hauteur.flags() | QgsMapLayer.Private)
        lst_diam.setFlags(lst_diam.flags() | QgsMapLayer.Private)

        essences.setDisplayExpression(''' CASE WHEN "selected" THEN '✅ ' ELSE '❌ ' END || "essence_variation" ''')
        lot.setDisplayExpression(''' 'LOT' || "LOT" || ' - ' || 'PRF' || "PARCELLE" ||  ': '  || "SURFACE" || ' ha' ''')
        param.setDisplayExpression(''' 'H' || "HMIN" || '-' || "HMAX" || 'D' || "DMIN" || '-' || "DMAX" ''')
        arbres.setDisplayExpression(
            """
            WITH_VARIABLE(
                'ess',
                get_feature(
                    'essences',
                    'fid',
                    coalesce(NULLIF("ESSENCE_ID", ''), "ESSENCE_SECONDAIRE_ID")
                ),
                concat(
                    "COMPTEUR",
                    ': ',
                    attribute(@ess, 'code'),
                    CASE
                        WHEN attribute(@ess, 'variation') IS NOT NULL
                        THEN concat(' ', attribute(@ess, 'variation'))
                        ELSE ''
                    END,
                    ' D', "DIAMETRE",
                    CASE
                        WHEN "HAUTEUR" IS NOT NULL AND "HAUTEUR" != ''
                        THEN concat(' H', "HAUTEUR")
                        ELSE ''
                    END,
                    CASE
                        WHEN "EFFECTIF" IS NOT NULL
                        THEN concat(' N', "EFFECTIF")
                        ELSE ''
                    END
                )
            )
            """
        )

        for key in (self.seq_vect_keys + self.seq_rast_keys):
            try:
                seq_read(key, self.seq_dir, add_to_project=True, style_folder=self.style_dir)
            except Exception as e:
                messageLog(f"Could not load layer {key}: {e}")

        fold()
        unfold("INVENTAIRE")

        return gpkg_path

    def _create_layers(self):

        layers = LayerFactory.create_all(TREE_MARKING_LAYERS)

        essences = load_essences(name = "Essences")
        layers["Essences"] = essences

        self.project.addMapLayers(list(layers.values()), addToLegend=False)

        self._init_essences(essences)
        self._init_param(layers["Param"])
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

    def _init_param(self, param):
        if not param.isEditable():
            param.startEditing()

        provider = param.dataProvider()

        provider.deleteFeatures([f.id() for f in param.getFeatures()])

        f = QgsFeature(param.fields())
        f["DMIN"] = self.dendro['dmin']
        f["DMAX"] = self.dendro['dmax']
        f["HMIN"] = self.dendro['hmin']
        f["HMAX"] = self.dendro['hmax']

        provider.addFeature(f)
        param.commitChanges()

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
    