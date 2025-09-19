from PyQt5.QtWidgets import QDialog, QMessageBox
from .expertise_create_dialog import Ui_ExpertiseCreateDialog
from .expertise_service import ExpertiseService

from ...core.db.manager import DatabaseManager

from ...utils.config import get_racines_path
from ...utils.variable import get_project_variable
from ...utils.utils import clear_project
from ...utils.ui import RasterController, QfieldPackager, SpeciesSelector, GridController

class ExpertiseCreateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_ExpertiseCreateDialog()
        self.ui.setupUi(self)
        self.essences_layer = DatabaseManager().load_essences("essences")

        # --- initialize from helpers class ---
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
        
        self.gha_tra_selector = SpeciesSelector(
            ui = self.ui, layer = self.essences_layer,
            choices="lw_species", selected="lw_selected_species",
            add="pb_add_species", remove="pb_remove_species",
            filter="le_filter_species"
        )

        self.tse_selector = SpeciesSelector(
            ui = self.ui, layer = self.essences_layer,
            choices="lw_species_taillis", selected="lw_selected_species_taillis",
            add="pb_add_species_taillis", remove="pb_remove_species_taillis",
            filter="le_filter_species_taillis"
        )
        tse_default = ["BOU", "CHA", "CHE", "ECH", "FRE", "HET", "NOI", "SAU", "TIL", "TRE"]
        tse_default_label = [name for name, code in self.tse_selector.essences_lookup.items() if code in tse_default]
        self.tse_selector.selected.addItems(tse_default_label)

        self.packager = QfieldPackager(
            self.ui,
            default_dir = get_racines_path("expertise", "Qfield", "Expertise"),
            package_ui = 'cb_package_for_qfield',
            outdir_ui = 'fw_outdir'
            )
        
        self.grid_controller = GridController(
            self.ui,
            create_grid_ui = 'cb_create_grid',
            points_per_ha_ui = 'dsp_points_per_ha'
        )

    def accept(self):

        if not self.gha_tra_selector.is_valid(): return
        if not self.tse_selector.is_valid(): return

        clear_project()

        codes_gha_tra = self.gha_tra_selector.selected_codes()
        codes_taillis = self.tse_selector.selected_codes()

        # 2) call service
        svc = ExpertiseService(
            codes=codes_gha_tra,
            codes_taillis=codes_taillis,
            dmin=self.ui.sp_dmin.value(),
            dmax=self.ui.sp_dmax.value(),
            hmin=self.ui.sp_hmin.value(),
            hmax=self.ui.sp_hmax.value(),
            essences_layer = self.essences_layer,
            grid_controller = self.grid_controller
        )

        try:
            svc.run()
            self.raster_controller.load_selected_rasters()

            msg = "Expertise complète !"
            if self.packager.is_valid():
                packaged_dir = self.packager.package(prefix="EXP", codes=codes_gha_tra)
                msg += f"\nProjet packagé dans :\n{packaged_dir}"
            QMessageBox.information(self, "Succès", msg)

            super().accept()

        except Exception as e:
            # everything else bubbles up here
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue :\n{e}")
