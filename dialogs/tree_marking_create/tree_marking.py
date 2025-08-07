from PyQt5.QtWidgets import QDialog, QMessageBox

from pathlib import Path

from .tree_marking_dialog import Ui_TreeMarkingCreateDialog
from .tree_marking_service import TreeMarkingService

from ...core.db.manager import DatabaseManager

from ...utils.config import get_racines_path
from ...utils.layers import load_vectors
from ...utils.variable import get_project_variable
from ...utils.ui import RasterController, SpeciesSelector, QfieldPackager
from ...utils.utils import clear_project

class TreeMarkingCreateDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_TreeMarkingCreateDialog()
        self.ui.setupUi(self)
        self.essences_layer = DatabaseManager().load_essences("essences")

        # --- initialize forest_name if forest is selected ---
        self.ui.le_forest_name.setText(get_project_variable("forest_prefix") or "Pas de forêt sélectionnée")

        # --- initialize from mixin ---
        raster_checkbox = {
            #   'key':     'checkbox_name',
                'plt_anc': 'cb_plt_anc',
                'plt':     'cb_plt',
                'mnh':     'cb_mnh',
                'scan25':  'cb_scan25',
                'irc':     'cb_irc',
                'rgb':     'cb_rgb',
            }
        self.raster_controller = RasterController(ui=self.ui, raster_checkbox=raster_checkbox)
        
        self.ess_selector = SpeciesSelector(
            ui = self.ui, layer = self.essences_layer,
            choices="lw_species", selected="lw_selected_species",
            add="pb_add_species", remove="pb_remove_species",
            filter="le_filter_species"
        )

        self.packager = QfieldPackager(
            self.ui,
            default_dir = get_racines_path("expertise", "Qfield", "Inventaire"),
            package_ui = 'cb_package_for_qfield',
            outdir_ui = 'fw_outdir'
            )

    def accept(self):

        if not self.ess_selector.is_valid():
            return

        clear_project()

        codes = self.ess_selector.selected_codes()
        # 2) call service
        svc = TreeMarkingService(
            codes=codes,
            dmin=self.ui.sp_dmin.value(),
            dmax=self.ui.sp_dmax.value(),
            hmin=self.ui.sp_hmin.value(),
            hmax=self.ui.sp_hmax.value(),
            essences_layer = self.essences_layer
        )

        try:
            svc.run()
            load_vectors("ua_polygon", group_name= "VECTOR")
            self.raster_controller.load_selected_rasters()

            msg = "Expertise complète !"
            if self.packager.is_valid():
                packaged_dir = self.packager.package(prefix="INV", codes=codes)
                msg += f"\nProjet packagé dans :\n{packaged_dir}"
            QMessageBox.information(self, "Succès", msg)

            super().accept()

        except Exception as e:
            # everything else bubbles up here
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue :\n{e}")
