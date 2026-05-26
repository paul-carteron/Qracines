
# Import from utils folder
from ....utils.layers import load_gpkg
from ....utils.config import get_qfield_path
from ....utils.variable import get_project_variable

from ..configurators.lot import LotConfigurator
from ..configurators.arbres import ArbresConfigurator
from ..configurators.param import ParamConfigurator

class TreeMarkingLoad:
    def __init__(self):
        self.gpkg_path = get_qfield_path("inventaire")
    
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

        return layers