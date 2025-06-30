from PyQt5.QtWidgets import (
    QDialog,
    QMessageBox,
    QAbstractItemView,
    QFileDialog
    )


from pathlib import Path

from .expertise_create_dialog import Ui_ExpertiseDialog

from ...core.db.manager import DatabaseManager
from ...core.expertise_service import ExpertiseService

from ...utils.path_manager import get_racines_path
from ...utils.variable_utils import clear_project, get_project_variable, set_project_variable
from ...utils.layer_utils import load_rasters, zoom_on_layer, load_vectors, replier

class ExpertiseCreateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_ExpertiseDialog()
        self.ui.setupUi(self)
       
        self.ui.le_forest_name.setText(get_project_variable("forest_prefix") or "Pas de forêt sélectionnée")

        # --- initialize diam/hauteur ---
        self.restore_dh_values()

        # --- initialize raster checkboxes ---
        self.raster_checkboxes = {
            "plt_anc": self.ui.cb_plt_anc,
            "plt":     self.ui.cb_plt,
            "mnh":     self.ui.cb_mnh,
            "scan25":  self.ui.cb_scan25,
            "irc":     self.ui.cb_irc,
            "rgb":     self.ui.cb_rgb,
        }
        self.restore_checkbox_states()
        
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
        self.restore_species_selection()

        # --- add/remove species functionnalities ---
        self.ui.pb_add_species.clicked.connect(self.add_selected_species)
        self.ui.pb_remove_species.clicked.connect(self.remove_selected_species)
        self.ui.pb_add_species_taillis.clicked.connect(self.add_selected_species_taillis)
        self.ui.pb_remove_species_taillis.clicked.connect(self.remove_selected_species_taillis)

        # --- connect buttons ---
        self.ui.buttonBox.accepted.disconnect(self.accept)
        self.ui.buttonBox.accepted.connect(self._on_accept)
        self.ui.buttonBox.rejected.connect(self.reject)
        
        # --- connect checkbox to toggle ---
        self.setup_connections()

    # region SAVE/RESTORE STATES
    def save_checkbox_states(self):
        for key, cb in self.raster_checkboxes.items():
            set_project_variable(f"ui_chk_{key}", cb.isChecked())

    def restore_checkbox_states(self):
        for key, cb in self.raster_checkboxes.items():
            val = get_project_variable(f"ui_chk_{key}")
            if val is not None:
                cb.setChecked(bool(val))

    def save_dh_values(self):
        set_project_variable("ui_dmin", self.ui.sp_dmin.value())
        set_project_variable("ui_dmax", self.ui.sp_dmax.value())
        set_project_variable("ui_hmin", self.ui.sp_hmin.value())
        set_project_variable("ui_hmax", self.ui.sp_hmax.value())

    def restore_dh_values(self):
        for key, spinbox in {
            "ui_dmin": self.ui.sp_dmin,
            "ui_dmax": self.ui.sp_dmax,
            "ui_hmin": self.ui.sp_hmin,
            "ui_hmax": self.ui.sp_hmax,
        }.items():
            val = get_project_variable(key)
            if val is not None:
                try:
                    spinbox.setValue(int(val))  # or float(val) if using QDoubleSpinBox
                except Exception:
                    pass

    def save_species_selection(self):
        gha_species = [self.ui.lw_selected_species.item(i).text() for i in range(self.ui.lw_selected_species.count())]
        taillis_species = [self.ui.lw_selected_species_taillis.item(i).text() for i in range(self.ui.lw_selected_species_taillis.count())]
        set_project_variable("ui_species_gha", ";".join(gha_species))
        set_project_variable("ui_species_taillis", ";".join(taillis_species))

    def restore_species_selection(self):
        gha_saved = get_project_variable("ui_species_gha")
        taillis_saved = get_project_variable("ui_species_taillis")

        if gha_saved:
            self.ui.lw_selected_species.clear()
            for name in gha_saved.split(";"):
                if name in self.essences_lookup:
                    self.ui.lw_selected_species.addItem(name)

        if taillis_saved:
            self.ui.lw_selected_species_taillis.clear()
            for name in taillis_saved.split(";"):
                if name in self.essences_lookup:
                    self.ui.lw_selected_species_taillis.addItem(name)
    # endregion

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

    def setup_connections(self):
        self.ui.cb_package_for_qfield.toggled.connect(self.toggle_fw_editability)

        self.ui.le_filter_species.textChanged.connect(self.update_species_lists)
        self.ui.le_filter_species_taillis.textChanged.connect(self.update_species_lists)

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

        self._species_all = self._taillis_all = sorted(unique_essences)

        self.update_species_lists()

        taillis_default_species = [name for name, code in self.essences_lookup.items() if code in self.taillis_default_codes]
        self.ui.lw_selected_species_taillis.addItems(taillis_default_species)

    def update_species_lists(self):
        filter_species = self.ui.le_filter_species.text().lower()
        filter_taillis = self.ui.le_filter_species_taillis.text().lower()

        self.ui.lw_species.clear()
        self.ui.lw_species_taillis.clear()

        self.ui.lw_species.addItems([s for s in self._species_all if filter_species in s.lower()])
        self.ui.lw_species_taillis.addItems([s for s in self._taillis_all if filter_taillis in s.lower()])  

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
            return None

        loaded_keys = load_rasters(*asked_keys, group_name="RASTER")
        if loaded_keys:
            zoom_on_layer(loaded_keys[0])

    def _on_accept(self):
        # 1) collect inputs
        outdir = Path(self.ui.fw_outdir.filePath())
        if not outdir.exists():
            QMessageBox.warning(self, "Dossier invalide", "Veuillez choisir un répertoire valide.")
            return

        # GHA/Transect check
        gha_empty = self.ui.lw_selected_species.count() == 0
        if gha_empty:
            QMessageBox.warning(self, "Espèces manquantes", "Veuillez sélectionner au moins une essence pour GHA/Transect.")
            return

        # Taillis check (use lw_selected_species_taillis)
        taillis_empty = self.ui.lw_selected_species_taillis.count() == 0
        if taillis_empty:
            QMessageBox.warning(self, "Espèces manquantes", "Veuillez sélectionner au moins une essence pour le Taillis.")
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
            packaged_dir = svc.run_full_diagnostic()
            load_vectors("ua_polygon", group_name= "VECTOR")
            self._load_selected_rasters()
            replier()

            if packaged_dir:
                QMessageBox.information(self, "Succès", f"Expertise complète !\nProjet packagé dans :\n{packaged_dir}")
            else:
                QMessageBox.information(self, "Succès", "Expertise complète !")

            self.accept()

        except Exception as e:
            # everything else bubbles up here
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue :\n{e}")

    def accept(self):
        self.save_checkbox_states()
        self.save_species_selection()
        self.save_dh_values()
        super().accept()

    def reject(self):
        self.save_checkbox_states()
        self.save_species_selection()
        self.save_dh_values()
        super().reject()