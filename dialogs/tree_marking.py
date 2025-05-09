from PyQt5.QtWidgets import QDialog, QMessageBox ,QAbstractItemView
from qgis.core import (
  QgsProject,
  QgsRasterLayer,
  )

from pathlib import Path

from .tree_marking_dialog import Ui_Tree_markingDialog

from ..core.db.manager import DatabaseManager
from ..core.tree_marking_service import TreeMarkingService

from ..utils.path_manager import get_path, get_style, find_similar_filenames, get_racines_path
from ..utils.qfield_utils import create_memory_layer, zip_folder_contents, add_layers_from_gpkg
from ..utils.variable_utils import create_new_projet_with_variables, get_project_variable

class Tree_markingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Tree_markingDialog()
        self.ui.setupUi(self)

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
        default_dir = Path(get_racines_path("expertise", "Inventaire"))
        default_dir.mkdir(parents=True, exist_ok=True)
        self.ui.fw_outdir.setFilePath(str(default_dir))
        self.ui.fw_outdir.setStorageMode(self.ui.fw_outdir.GetDirectory)

        # ---- initialize species list ----
        self.ui.lw_selected_species.setSelectionMode(QAbstractItemView.MultiSelection)
        self.ui.lw_species.setSelectionMode(QAbstractItemView.MultiSelection)
        self.essences_layer = DatabaseManager().load_essences("essences")
        self.populate_species_list()

        # --- add/remove species functionnalities ---
        self.ui.pb_add_species.clicked.connect(self.add_selected_species)
        self.ui.pb_remove_species.clicked.connect(self.remove_selected_species)

        # --- connect buttons ---
        self.ui.buttonBox.accepted.connect(self._on_accept)
        self.ui.buttonBox.rejected.connect(self.reject)
        
         # --- connect checkbox to toggle ---
        self.setup_connections()

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

    @staticmethod
    def is_in_list(list_widget, text):
        return any(list_widget.item(i).text() == text for i in range(list_widget.count()))

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

    def _get_codes(self):
        all_essences = [self.ui.lw_selected_species.item(i).text()for i in range(self.ui.lw_selected_species.count())]
        codes = [self.essences_lookup[ess] for ess in all_essences if ess in self.essences_lookup]
        return codes

    def _load_selected_rasters(self):
        project = QgsProject.instance()
        root = project.layerTreeRoot()

        for logical_key, checkbox in self.raster_checkboxes.items():
            if checkbox.isChecked():
                try:
                    # Get and check raster path
                    raster_path = Path(get_path(logical_key))
                    if not raster_path.exists():
                        QMessageBox.information(
                            self, "Raster manquant",
                            f"Le fichier raster pour {logical_key} est introuvable :\n{raster_path}"
                        )
                        continue

                    # Load raster layer
                    layer = QgsRasterLayer(str(raster_path), logical_key)
                    if not layer.isValid():
                        raise Exception(f"Raster invalide : {raster_path}")

                    # Optionally load style
                    try:
                        style_path = Path(get_style(logical_key))
                        layer.loadNamedStyle(str(style_path))
                        layer.triggerRepaint()
                    except (KeyError, ValueError, FileNotFoundError):
                        pass  # Style is optional

                    # Add layer and move it to the bottom of the layer tree
                    project.addMapLayer(layer, addToLegend=True)
                    layer_node = root.findLayer(layer.id())
                    if layer_node:
                        root.insertChildNode(-1, root.takeChildNode(root.children().index(layer_node)))

                except Exception as e:
                    QMessageBox.warning(
                        self, "Erreur de chargement",
                        f"Impossible de charger {logical_key} : {str(e)}"
                    )

    def _on_accept(self):
        # 1) collect inputs
        outdir = Path(self.ui.fw_outdir.filePath())
        if not outdir.exists():
            QMessageBox.warning(self, "Dossier invalide", "Veuillez choisir un répertoire valide.")
            return

        dmin, dmax = self.ui.sp_dmin.value(), self.ui.sp_dmax.value()
        hmin, hmax = self.ui.sp_hmin.value(), self.ui.sp_hmax.value()

        create_new_projet_with_variables()

        # 2) call service
        svc = TreeMarkingService(
            output_dir=outdir,
            package_for_qfield=self.ui.cb_package_for_qfield.isChecked(),
            codes=self._get_codes(),
            dmin=dmin, dmax=dmax,
            hmin=hmin, hmax=hmax,
        )

        try:
            self.load_selected_rasters()
            packaged_dir = svc.run_full_diagnostic()

            if packaged_dir:
                QMessageBox.information(self, "Succès", f"Inventaire complet !\nProjet packagé dans :\n{packaged_dir}")
            else:
                QMessageBox.information(self, "Succès", "Inventaire complet !")

            self.accept()

        except Exception as e:
            # everything else bubbles up here
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue :\n{e}")
