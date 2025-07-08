from PyQt5.QtWidgets import QCheckBox, QAbstractItemView, QListWidget, QPushButton, QLineEdit, QMessageBox
from qgis.gui import QgsFileWidget
from ..utils.variable_utils import get_project_variable
from ..utils.layer_utils import load_rasters, zoom_on_layer, replier

import unicodedata
from pathlib import Path
from typing import Type, Any

class UIBinderMixin:
    """
    Provides a `_bind_widget(name, cls)` helper for looking up
    self.ui.<name> and type-checking it.
    """

    def _bind_widget(self, name: str, cls: Type[Any]) -> Any:
        """
        Look up self.ui.<ui_name>, assert it’s an instance of cls,
        then return it (or raise AttributeError).
        """
        w = getattr(self.ui, name, None)
        if not isinstance(w, cls):
            raise AttributeError(f"Expected {cls.__name__} at ui.{name}")
        return w

class RasterController(UIBinderMixin):

    def __init__(self, ui, raster_checkbox):
        self.ui  = ui
        self.cbs = {key: self._bind_widget(attr, QCheckBox) for key, attr in raster_checkbox.items()}

        is_forest_selected = bool(get_project_variable("forest_prefix"))
        if not is_forest_selected:
            # Disable + uncheck all
            for cb in self.cbs.values():
                cb.setChecked(False)
                cb.setEnabled(False)
            return

    def load_selected_rasters(self):
        asked_keys = [key for key, cb in self.cbs.items() if cb.isChecked()]
        if not asked_keys:
            return

        loaded_keys = load_rasters(*asked_keys, group_name="RASTER")
        if loaded_keys:
            zoom_on_layer(loaded_keys[0])
        
        replier()

class QfieldPackager(UIBinderMixin):
        
    def __init__(self, ui, package_ui, outdir_ui, default_dir):
        self.ui= ui

        # 1) bind widgets
        self.outdir_ui  = self._bind_widget(outdir_ui, QgsFileWidget)
        self.package_ui = self._bind_widget(package_ui, QCheckBox)

        # 2) set default directory
        try:
            default_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            QMessageBox.warning(None, "Erreur disque", f"Impossible de créer\n{default_dir}:\n{e}")

        # 3) configure file-widget
        self.outdir_ui.setStorageMode(self.outdir_ui.GetDirectory)
        self.outdir_ui.setFilePath(str(default_dir))

        # 4) wire toggle
        self.package_ui.toggled.connect(self._on_toggle)
    
    def _on_toggle(self, checked):
        self.outdir_ui.setEnabled(checked)

    def get_qfield_outdir(self):
        qfield_outdir = Path(self.outdir_ui.filePath())
        if not qfield_outdir.exists():
            QMessageBox.warning(self, "Dossier invalide", "Veuillez choisir un répertoire valide.")
            return
        return qfield_outdir

class SpeciesSelector(UIBinderMixin):
    def __init__(self,
              *,
              ui,
              layer,
              choices: str,
              selected: str,
              add: str,
              remove: str,
              filter: str):
        
        self.ui       = ui
        self.layer    = layer
        
        self.choices  = self._bind_widget(choices, QListWidget)
        self.selected = self._bind_widget(selected, QListWidget)
        self.add      = self._bind_widget(add, QPushButton)
        self.remove   = self._bind_widget(remove, QPushButton)
        self.filter   = self._bind_widget(filter, QLineEdit)

        # 3) Configure selection modes
        self.choices.setSelectionMode(QAbstractItemView.MultiSelection)
        self.selected.setSelectionMode(QAbstractItemView.MultiSelection)

        # 4) Populate the “choices” list
        self.populate_species_list()

        # 5) Wire up buttons
        self.filter.textChanged.connect(self.on_filter)
        self.add.clicked.connect(self.on_add)
        self.remove.clicked.connect(self.on_remove)

    def populate_species_list(self) -> None:
        """
        Fill the 'choices' QListWidget from self.essences_layer.
        Expects self.essences_layer.getFeatures() to yield features
        with 'essence' and 'code' attributes.
        """

        # This create unique list of code essence because dict cant' have duplicate names
        self.essences_lookup = {feat['essence']: feat['code'] for feat in self.layer.getFeatures()}
        self.choices.clear()
        self.choices.addItems(sorted(self.essences_lookup))

    @staticmethod
    def _item_exists(list_widget: QListWidget, text: str) -> bool:
        return any(list_widget.item(i).text() == text for i in range(list_widget.count()))

    @staticmethod
    def _strip_accents(text: str) -> str:
        """Remove diacritic marks (accents) from a Unicode string."""
        # Normalize text to separate base letters and accents, then remove combining marks.
        normalized = unicodedata.normalize('NFD', text)  
        return ''.join(ch for ch in normalized if unicodedata.category(ch) != 'Mn')

    def on_filter(self):
        filter_species = self._strip_accents(self.filter.text().lower())
        self.choices.clear()
        self.choices.addItems([s for s in self.essences_lookup.keys() if filter_species in self._strip_accents(s.lower())])
    
    def on_add(self) -> None:
        for item in self.choices.selectedItems():
            txt = item.text()
            if not self._item_exists(self.selected, txt):
                self.selected.addItem(txt)
        self.filter.clear()

    def on_remove(self) -> None:
        for item in self.selected.selectedItems():
            row = self.selected.row(item)
            self.selected.takeItem(row)

    def selected_codes(self) -> list:
        """
        Return the list of codes for currently selected species, based on essences_lookup.
        """
        all_essences = [self.selected.item(i).text() for i in range(self.selected.count())]
        codes = [self.essences_lookup[ess] for ess in all_essences if ess in self.essences_lookup]
        return codes
  
    def is_valid(self) -> bool:
        """
        Ensure at least one species is selected. Pop up a warning if empty.
        Returns True if OK, False if empty.
        """
        if self.selected.count() == 0:
            QMessageBox.warning(None,"Espèces manquantes",f"Veuillez sélectionner au moins une essence dans chaque selecteur d'essence.")
            return False
        return True
    

