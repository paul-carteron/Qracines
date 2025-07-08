from PyQt5.QtWidgets import QDialog, QMessageBox

from pathlib import Path

from .tree_marking_dialog import Ui_TreeMarkingCreateDialog
from .tree_marking_service import TreeMarkingService
from ..base import RasterCheckboxMixin, SpeciesSelectionMixin, QfieldPackageMixin

from ...core.db.manager import DatabaseManager

from ...utils.path_manager import get_racines_path
from ...utils.variable_utils import clear_project, get_project_variable
from ...utils.layer_utils import load_rasters, zoom_on_layer, replier

class TreeMarkingCreateDialog(QDialog, QfieldPackageMixin, RasterCheckboxMixin, SpeciesSelectionMixin):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_TreeMarkingCreateDialog()
        self.ui.setupUi(self)
        self.essences_layer = DatabaseManager().load_essences("essences")

        # --- initialize forest_name if forest is selected ---
        self.ui.le_forest_name.setText(get_project_variable("forest_prefix") or "Pas de forêt sélectionnée")

        # --- initialize from mixin ---
        self.init_raster_checkboxes(
            raster_checkbox = {
            #   'key':     'checkbox_name',
                'plt_anc': 'cb_plt_anc',
                'plt':     'cb_plt',
                'mnh':     'cb_mnh',
                'scan25':  'cb_scan25',
                'irc':     'cb_irc',
                'rgb':     'cb_rgb',
            })
        self.init_species_selection(
            choices =  'lw_species', 
            selected = 'lw_selected_species',
            add =      'pb_add_species', 
            remove =   'pb_remove_species',
            filter =   'le_filter_species'
            )
        self.init_qfield_package(
            package_ui = 'cb_package_for_qfield',
            outdir_ui = 'fw_outdir',
            default_dir = get_racines_path("expertise", "Inventaire")
        )

        # --- connect buttons ---
        self.ui.buttonBox.accepted.connect(self._on_accept)

    def _on_accept(self):

        clear_project()

        # 2) call service
        svc = TreeMarkingService(
            output_dir=self.get_qfield_outdir(),
            package_for_qfield=self.ui.cb_package_for_qfield.isChecked(),
            codes=self.selected_codes(),
            dmin=self.ui.sp_dmin.value(),
            dmax=self.ui.sp_dmax.value(),
            hmin=self.ui.sp_hmin.value(),
            hmax=self.ui.sp_hmax.value(),
        )

        try:
            packaged_dir = svc.run_full_diagnostic()
            self.load_selected_rasters()
            replier()

            if packaged_dir:
                QMessageBox.information(self, "Succès", f"Inventaire complet !\nProjet packagé dans :\n{packaged_dir}")
            else:
                QMessageBox.information(self, "Succès", "Inventaire complet !")

            self.accept()

        except Exception as e:
            # everything else bubbles up here
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue :\n{e}")
