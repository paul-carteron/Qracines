from PyQt5.QtWidgets import (
    QDialog,
    QMessageBox,
    QAbstractItemView,
    QFileDialog
    )


from pathlib import Path

from .expertise_dialog import Ui_ExpertiseDialog
from .expertise_import import Ui_ExpertiseImportDialog

from ..core.db.manager import DatabaseManager
from ..core.expertise_service import ExpertiseService

from ..utils.path_manager import get_racines_path, get_display_name
from ..utils.variable_utils import clear_project, get_project_variable
from ..utils.layer_utils import load_rasters, zoom_on_layer

class ExpertiseDialog(QDialog):
    def __init__(self, mode="create", parent=None):
        super().__init__(parent)
        self.mode = mode

        if self.mode == "create":
            self.ui = Ui_ExpertiseDialog()
        elif self.mode == "import":
            self.ui = Ui_ExpertiseImportDialog()
            print("yo import")
        else:
            raise ValueError(f"Unknown mode: {mode}")
        
        self.ui.setupUi(self)
        
        if self.mode == "import":
            self.ui.pb_import_files.clicked.connect(self.import_files)
        else:
            # --- initialize forest_name if forest is selected ---
            self.ui.le_forest_name.setText(get_project_variable("forest_prefix") or "Pas de forêt sélectionnée")

            # --- initialize raster checkboxes ---
            self.raster_checkboxes = {
                "plt_anc": self.ui.cb_plt_anc,
                "plt":     self.ui.cb_plt,
                "mnh":     self.ui.cb_mnh,
                "scan25":  self.ui.cb_scan25,
                "irc":     self.ui.cb_irc,
                "rgb":     self.ui.cb_rgb,
            }
            self.update_raster_checkbox_states()

            # --- initialise default output directory ---
            default_dir = get_racines_path("expertise", "Expertise")
            default_dir.mkdir(parents=True, exist_ok=True)
            self.ui.fw_outdir.setFilePath(str(default_dir))
            self.ui.fw_outdir.setStorageMode(self.ui.fw_outdir.GetDirectory)

            # ---- initialize species list ----
            ## Gha / Transect
            self.ui.lw_selected_species.setSelectionMode(QAbstractItemView.MultiSelection)
            self.ui.lw_species.setSelectionMode(QAbstractItemView.MultiSelection)

            ## Taillis
            self.ui.lw_selected_species_taillis.setSelectionMode(QAbstractItemView.MultiSelection)
            self.ui.lw_species_taillis.setSelectionMode(QAbstractItemView.MultiSelection)
            self.taillis_default_codes = ["BOU", "CHA", "CHE", "ECH", "FRE", "HET", "NOI", "SAU", "TIL", "TRE"]
            
            self.essences_layer = DatabaseManager().load_essences("essences")
            self.populate_species_list()

            # --- add/remove species functionnalities ---
            self.ui.pb_add_species.clicked.connect(self.add_selected_species)
            self.ui.pb_remove_species.clicked.connect(self.remove_selected_species)
            self.ui.pb_add_species_taillis.clicked.connect(self.add_selected_species_taillis)
            self.ui.pb_remove_species_taillis.clicked.connect(self.remove_selected_species_taillis)

            # --- connect buttons ---
            self.ui.buttonBox.accepted.connect(self._on_accept)
            self.ui.buttonBox.rejected.connect(self.reject)
            
            # --- connect checkbox to toggle ---
            self.setup_connections()


    def import_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Sélectionner des fichiers à importer",
            "",  # starting directory
            "GeoPackage (*.gpkg);;Shapefiles (*.shp);;All files (*.*)"
        )
        if files:
            print("Fichiers sélectionnés:", files)
            self.ui.lw_selected_files.addItems(files)


    def update_raster_checkbox_states(self):
        forest_selected = bool(get_project_variable("forest_prefix"))
        # These logical keys get auto-checked when a forest exists
        auto_check = {"plt_anc", "plt"} if forest_selected else set()

        for logical_key, cb in self.raster_checkboxes.items():
            cb.setEnabled(forest_selected)
            cb.setChecked(logical_key in auto_check)

    def setup_connections(self):
        self.ui.cb_package_for_qfield.toggled.connect(self.toggle_fw_editability)

    def toggle_fw_editability(self, checked):
        self.ui.fw_outdir.setEnabled(checked)

    # region species_list
    @staticmethod
    def is_in_list(list_widget, text):
        return any(list_widget.item(i).text() == text for i in range(list_widget.count()))
    
    def populate_species_list(self):
        self.essences_lookup = {}

        unique_essences = []

        for feat in self.essences_layer.getFeatures():
            name = feat["essence"]
            code = feat["code"]
            if name not in self.essences_lookup:
                self.essences_lookup[name] = code
                unique_essences.append(name)

        self.ui.lw_species.addItems(unique_essences)
        self.ui.lw_species_taillis.addItems(unique_essences)

        taillis_default_species = [name for name, code in self.essences_lookup.items() if code in self.taillis_default_codes]
        self.ui.lw_selected_species_taillis.addItems(taillis_default_species)

    def add_selected_species(self):
        selected_items = self.ui.lw_species.selectedItems()
        for item in selected_items:
            text = item.text()
            if not self.is_in_list(self.ui.lw_selected_species, text):
                self.ui.lw_selected_species.addItem(text)

    def remove_selected_species(self):
        for item in self.ui.lw_selected_species.selectedItems():
            row = self.ui.lw_selected_species.row(item)
            self.ui.lw_selected_species.takeItem(row)

    def add_selected_species_taillis(self):
        selected_items = self.ui.lw_species_taillis.selectedItems()
        for item in selected_items:
            text = item.text()
            if not self.is_in_list(self.ui.lw_selected_species_taillis, text):
                self.ui.lw_selected_species_taillis.addItem(text)

    def remove_selected_species_taillis(self):
        for item in self.ui.lw_selected_species_taillis.selectedItems():
            row = self.ui.lw_selected_species_taillis.row(item)
            self.ui.lw_selected_species_taillis.takeItem(row)
    # endregion

    def _get_codes(self):
        all_essences = [self.ui.lw_selected_species.item(i).text() for i in range(self.ui.lw_selected_species.count())]
        codes = [self.essences_lookup[ess] for ess in all_essences if ess in self.essences_lookup]
        return codes
    
    def _load_selected_rasters(self):
        asked_keys = [key for key, cb in self.raster_checkboxes.items() if cb.isChecked()]
        if not asked_keys:
            return

        loaded_keys = load_rasters(*asked_keys, group_name="RASTER")
        if loaded_keys:
            zoom_on_layer(loaded_keys[0])

    def _on_accept(self):
        # 1) collect inputs
        outdir = Path(self.ui.fw_outdir.filePath())
        if not outdir.exists():
            QMessageBox.warning(self, "Dossier invalide", "Veuillez choisir un répertoire valide.")
            return

        dmin, dmax = self.ui.sp_dmin.value(), self.ui.sp_dmax.value()
        hmin, hmax = self.ui.sp_hmin.value(), self.ui.sp_hmax.value()

        clear_project()

        # 2) call service
        svc = ExpertiseService(
            output_dir=outdir,
            package_for_qfield=self.ui.cb_package_for_qfield.isChecked(),
            codes=self._get_codes(),
            codes_taillis=self.taillis_default_codes,
            dmin=dmin, dmax=dmax,
            hmin=hmin, hmax=hmax,
            essences_layer = self.essences_layer
        )

        try:
            self._load_selected_rasters()
            packaged_dir = svc.run_full_diagnostic()

            if packaged_dir:
                QMessageBox.information(self, "Succès", f"Expertise complète !\nProjet packagé dans :\n{packaged_dir}")
            else:
                QMessageBox.information(self, "Succès", "Expertise complète !")

            self.accept()

        except Exception as e:
            # everything else bubbles up here
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue :\n{e}")
