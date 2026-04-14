import processing

from qgis.utils import iface
from qgis.core import QgsVectorLayer, QgsProcessing, QgsProject
from PyQt5.QtWidgets import QMessageBox, QDialog
from qgis.PyQt import uic

# Import from utils folder
from ....utils.layers import load_gpkg
from ....utils.processing import calculate_essence_id, merge_with_ess, save_as_xlsx
from ....utils.ui import GpkgLoader
from ....utils.config import get_new_to_old, get_qfield_path
from ....utils.message import messageLog
from ....utils.variable import get_project_variable

from ..config import TYPE_CHOICES, MARQUAGE_CHOICES, COULEUR_CHOICES, MARTEAU_CHOICES
from ..configurators.param import ParamConfigurator
from ..configurators.arbres import ArbresConfigurator
from ..layer_schema import TREE_MARKING_LAYERS

class TreeMarkingLoad:
    def __init__(self):
        self.gpkg_path = get_qfield_path("inventaire")
    
    def load(self):

        layers = load_gpkg(self.gpkg_path, group_name="INVENTAIRE")

        arbres = layers.get("Arbres")
        param = layers.get("Param")
        ess = layers.get("Essences")
        lst_hauteur = layers.get("lst_hauteur")
        lst_diam = layers.get("lst_diam")

        if not all([arbres, param, ess]):
            raise RuntimeError("Layers manquants dans le GPKG")

        seq_id = get_project_variable("QS2_seq_id") or None

        ParamConfigurator(param, seq_id=seq_id).configure()
        ArbresConfigurator(arbres, param, ess, lst_hauteur, lst_diam).configure()

        # --- 3. Reapply layer properties (not stored reliably)
        ess.setDisplayExpression(
            '''CASE WHEN "selected" THEN '✅ ' ELSE '❌ ' END || "essence_variation"'''
        )

        param.setDisplayExpression('"PARCELLE" || "SURFACE"')

        return layers