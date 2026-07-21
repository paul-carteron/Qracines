from Qracines.utils.message import messageLog
import processing

from qgis.core import QgsProject, QgsProcessing, QgsMapLayer, QgsField, QgsFeature
from qgis.PyQt.QtCore import QVariant
from qgis.utils import iface

from Qracines.core.layer.factory import LayerFactory

from Qracines.utils.layers import load_gpkg, create_relation, set_relation_label
from Qracines.utils.utils import fold, unfold
from Qracines.utils.essence import load_essences
from ..layer_schema import EXPERTISE_LAYERS

# configurators
from ..configurators.placette import PlacetteConfigurator
from ..configurators.transect import TransectConfigurator
from ..configurators.limite import LimiteConfigurator
from ..configurators.gha import GhaConfigurator
from ..configurators.tse import TseConfigurator
from ..configurators.va import VaConfigurator
from ..configurators.reg import RegConfigurator
from ..configurators.param import ParamConfigurator
from ..configurators.essences import EssencesConfigurator

from qsequoia2.modules.utils.seq_config import seq_read

_SKIP_VARIATIONS = {"foudroyé", "nécrosé", "dépérissant"}

class ExpertiseCreateService:

    def __init__(
        self,
        seq_dir,
        style_dir,
        codes: list,
        codes_taillis: list,
        seq_vect_keys: list,
        seq_rast_keys: list,
        dendro_controller,
        grid_controller,
    ):

        self.iface = iface
        self.project = QgsProject.instance()

        self.seq_dir = seq_dir
        self.style_dir = style_dir

        self.codes = codes
        self.codes_taillis = codes_taillis
        self.seq_vect_keys = seq_vect_keys
        self.seq_rast_keys = seq_rast_keys
        self.dendro = dendro_controller.get_values()

        self.grid_controller = grid_controller

    def run(self):
        
        layers = self._create_layers()
        gpkg_path = self._package_layers(layers)

        layers = load_gpkg(gpkg_path, group_name="EXPERTISE")

        relations = self._create_relations(layers)

        self._configure_layers(layers, relations)
        self._configure_flags(layers)
        self._configure_display_expression(layers)

        for key in (self.seq_vect_keys + self.seq_rast_keys):
            try:
                seq_read(key, self.seq_dir, add_to_project=True, style_folder=self.style_dir)
            except Exception as e:
                messageLog(f"Could not load layer {key}: {e}")

        fold()
        unfold("EXPERTISE")

        return gpkg_path

    def _create_layers(self):

        layers = LayerFactory.create_all(EXPERTISE_LAYERS)

        essences = load_essences(name = "essences")
        layers["essences"] = essences

        if self.grid_controller.is_valid():
            layers["Grid"] = self.grid_controller.create_grid(self.seq_dir)

        self.project.addMapLayers(list(layers.values()), addToLegend=False)

        self._init_essences(layers["essences"])
        self._init_param(layers["param"])
        self._init_range_layer(layers["lst_hauteur"], 0, 50)
        self._init_range_layer(layers["lst_diam"], 5, 150, 5)

        return layers

    def _init_essences(self, layer):

        messageLog("_init_essences")
        # ajouter champ si absent
        if layer.fields().indexOf("selected") == -1:
            layer.dataProvider().addAttributes([QgsField("selected", QVariant.Bool)])
            layer.updateFields()

        if not layer.isEditable():
            layer.startEditing()

        selected_idx = layer.fields().indexOf("selected")
        messageLog(f"selected_idx: {selected_idx}")
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
        param = layers["param"]

        ParamConfigurator(param).configure()
        EssencesConfigurator(essences).configure()

        placette = layers["placette"]
        transect = layers["transect"]
        limite = layers["limite"]
        gha = layers["gha"]
        tse = layers["tse"]
        va = layers["va"]
        reg = layers["reg"]
        lst_hauteur = layers["lst_hauteur"]
        lst_diam = layers["lst_diam"]

        PlacetteConfigurator(placette, relations).configure()
        TransectConfigurator(transect, self.dendro, essences, lst_hauteur, lst_diam).configure()
        LimiteConfigurator(limite).configure()
        GhaConfigurator(gha, essences).configure()
        TseConfigurator(tse, essences,self.codes_taillis).configure()
        VaConfigurator(va, essences).configure()
        RegConfigurator(reg, essences).configure()

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

        private_layers = ["lst_hauteur", "lst_diam", "gha", "tse", "va", "reg"]
        for layer in private_layers:
            l = layers[layer]
            l.setFlags(l.flags() | QgsMapLayer.Private)


    def _configure_display_expression(self, layers):

        essences = layers["essences"]
        param = layers["param"]

        essences.setDisplayExpression(''' CASE WHEN "selected" THEN '✅ ' ELSE '❌ ' END || "essence_variation" ''')
        param.setDisplayExpression(''' 'H' || "HMIN" || '-' || "HMAX" || 'D' || "DMIN" || '-' || "DMAX" ''')

