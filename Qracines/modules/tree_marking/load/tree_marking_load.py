
# Import from utils folder
from pathlib import Path
from random import randrange

from qgis.PyQt.QtGui import QColor
from qgis.core import QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsVectorLayerUtils, QgsMapLayer

from Qracines.utils.message import messageLog

from ....utils.layers import load_gpkg
from ....utils.config import get_qfield_path

from ..configurators.lot import LotConfigurator
from ..configurators.arbres import ArbresConfigurator
from ..configurators.param import ParamConfigurator

from qsequoia2.modules.utils.seq_config import seq_read
from qsequoia2.modules.utils.variable import get_global_variable, get_project_variable

class TreeMarkingLoad:
    def __init__(self):
        self.gpkg_path = get_qfield_path("inventaire")
    
    @staticmethod
    def update_categories(layer, diameter_field="DIAMETRE"):

        renderer = layer.renderer().clone()
        if not isinstance(renderer, QgsCategorizedSymbolRenderer):
            return False

        values, ok = QgsVectorLayerUtils.getValues(layer, renderer.classAttribute(), False)
        if not ok:
            return False

        symbols = {
            cat.value(): cat.symbol().clone()
            for cat in renderer.categories()
            if cat.symbol()
        }

        summary = {}

        for feature, value in zip(layer.getFeatures(), values):
            diameter = feature[diameter_field]

            if value in (None, "") or diameter in (None, ""):
                continue

            diameter = int(diameter)
            s = summary.setdefault(value, {"n": 0, "min": diameter, "max": diameter})

            s["n"] += 1
            s["min"] = min(s["min"], diameter)
            s["max"] = max(s["max"], diameter)

        def label(value):
            s = summary[value]
            diam = f'{s["min"]} cm' if s["min"] == s["max"] else f'{s["min"]}-{s["max"]} cm'
            return f'{value} ({s["n"]} arbres, {diam})'

        def symbol(value):
            sym = symbols.get(value, renderer.sourceSymbol()).clone()

            if value not in symbols:
                sym.setColor(QColor(randrange(256), randrange(256), randrange(256)))

            return sym

        renderer.deleteAllCategories()

        for value in sorted(summary, key=str):
            renderer.addCategory(
                QgsRendererCategory(value, symbol(value), label(value), True)
            )

        layer.setRenderer(renderer)
        layer.triggerRepaint()

        return True

    def load(self):

        layers = load_gpkg(self.gpkg_path, group_name="INVENTAIRE")

        arbres = layers.get("Arbres")
        param = layers.get("Param")
        lot = layers.get("Lot")
        ess = layers.get("Essences")
        lst_hauteur = layers.get("lst_hauteur")
        lst_diam = layers.get("lst_diam")

        if not all([arbres, param, lot, ess]):
            raise RuntimeError("Layers manquants dans le GPKG")

        seq_id = get_project_variable("QS2_seq_id") or None

        ParamConfigurator(param).configure()
        LotConfigurator(lot, seq_id=seq_id).configure()
        ArbresConfigurator(arbres, lot, ess, lst_hauteur, lst_diam).configure()

        # --- 3. Reapply layer properties (not stored reliably)
        ess.setDisplayExpression(
            '''CASE WHEN "selected" THEN '✅ ' ELSE '❌ ' END || "essence_variation"'''
        )

        lot.setDisplayExpression('"LOT" || " - " || "PARCELLE" ||  ": "  || "SURFACE" || " ha"')

        # --- Apply internal styles if available
        style_directory = get_global_variable("QS2_styles_directory")
        style_name = "INV_Arbres.qml"

        if arbres and style_directory:
            styles = list(Path(style_directory).rglob(style_name))

            if styles:
                msg, ok = arbres.loadNamedStyle(str(styles[0]), QgsMapLayer.AllStyleCategories)
                messageLog(f"[STYLE] {msg}")

                if ok:
                    self.update_categories(arbres)
                else:
                    messageLog(f"[STYLE] Failed to load {styles[0]}", level="e")
            else:
                messageLog(f"[STYLE] Missing {style_name}", level="w")

        seq_dir = get_project_variable("QS2_seq_dir")
        messageLog(f"[SEQ] seq_dir: {seq_dir}")
        if seq_dir:
            plt = seq_read("r.seq.plt", seq_dir=seq_dir, add_to_project=True)
            if plt and plt.renderer():
                plt.renderer().setOpacity(0.6)
                plt.triggerRepaint()

        return layers