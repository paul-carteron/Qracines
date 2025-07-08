from PyQt5.QtWidgets import QCheckBox, QAbstractItemView, QListWidget, QPushButton, QLineEdit, QMessageBox
from qgis.gui import QgsFileWidget
from ..utils.variable_utils import get_project_variable, set_project_variable
from ..utils.layer_utils import load_rasters, zoom_on_layer

import unicodedata
from pathlib import Path

class RasterCheckboxMixin:
    """
    Mixin for dialogs that need to initialize, restore and save a fixed set of
    raster‐option QCheckBox widgets based on class‐level configuration.

    Subclasses must define:
      • NAMESPACE (str): prefix for persistence keys
      • RASTER_CHECKBOX (tuple[str, ...]):
          attribute names on self.ui for each QCheckBox, e.g.
          ('cb_plt_anc','cb_plt','cb_mnh','cb_scan25','cb_irc','cb_rgb')
    """

    def _bind_widget(self, ui_name, cls):
        """
        Look up self.ui.<ui_name>, assert it’s an instance of cls, 
        then return it (or raise a clear AttributeError).
        """
        w = getattr(self.ui, ui_name, None)
        if not isinstance(w, cls):
            raise AttributeError(f"Expected {cls.__name__} at self.ui.{ui_name}")
        return w

    def init_raster_checkboxes(self, raster_checkbox) -> None:
        forest_selected = bool(get_project_variable("forest_prefix"))

        # Validate all widgets exist, are QCheckBox and save them in cbs (checkboxes)
        cbs = {key: self._bind_widget(attr, QCheckBox) for key, attr in raster_checkbox.items()}

        if not forest_selected:
            # Disable + uncheck all
            for cb in cbs.values():
                cb.setChecked(False)
                cb.setEnabled(False)
            return

        # Remember them for saving later
        self.cbs = cbs

    def load_selected_rasters(self):
        asked_keys = [key for key, cb in self.cbs.items() if cb.isChecked()]
        if not asked_keys:
            return

        loaded_keys = load_rasters(*asked_keys, group_name="RASTER")
        if loaded_keys:
            zoom_on_layer(loaded_keys[0])

class SpeciesSelectionMixin:
    """
    Mixin to wire up a pair of QListWidgets for species selection:
      - one for available choices
      - one for currently selected items

    After init_species_selection():
      • self.choices  → QListWidget for all species
      • self.selected → QListWidget for chosen species
      • self.add  → QPushButton to add from choices → selected
      • self.remove → QPushButton to remove from selected
    """

    def _bind_widget(self, ui_name, cls):
        """
        Look up self.ui.<ui_name>, assert it’s an instance of cls, 
        then return it (or raise a clear AttributeError).
        """
        w = getattr(self.ui, ui_name, None)
        if not isinstance(w, cls):
            raise AttributeError(f"Expected {cls.__name__} at self.ui.{ui_name}")
        return w

    def init_species_selection(self, choices, selected, add, remove, filter) -> None:
        if not hasattr(self, 'essences_layer'):
          raise AttributeError(f"{self.__class__.__name__} must set `self.essences_layer` before calling init_species_selection()")
        
        # 2) Grab widgets and expose them as attributes
        self.choices =  self._bind_widget(choices, QListWidget)
        self.selected = self._bind_widget(selected, QListWidget)
        self.add =      self._bind_widget(add, QPushButton)
        self.remove =   self._bind_widget(remove, QPushButton)
        self.filter =   self._bind_widget(filter, QLineEdit)

        # 3) Configure selection modes
        self.choices.setSelectionMode(QAbstractItemView.MultiSelection)
        self.selected.setSelectionMode(QAbstractItemView.MultiSelection)

        # 4) Populate the “choices” list
        self.populate_species_list()

        # 5) Wire up buttons
        self.add.clicked.connect(self.on_add)
        self.remove.clicked.connect(self.on_remove)
        self.filter.textChanged.connect(self.update_species_lists)

    def populate_species_list(self) -> None:
        """
        Fill the 'choices' QListWidget from self.essences_layer.
        Expects self.essences_layer.getFeatures() to yield features
        with 'essence' and 'code' attributes.
        """

        # This create unique list of code essence because dict cant' have duplicate names
        self.essences_lookup = {feat['essence']: feat['code'] for feat in self.essences_layer.getFeatures()}
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

    def update_species_lists(self):
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
  
class QfieldPackageMixin:
    
    def _bind_widget(self, ui_name, cls):
        """
        Look up self.ui.<ui_name>, assert it’s an instance of cls, 
        then return it (or raise a clear AttributeError).
        """
        w = getattr(self.ui, ui_name, None)
        if not isinstance(w, cls):
            raise AttributeError(f"Expected {cls.__name__} at self.ui.{ui_name}")
        return w
    
    def init_qfield_package(self, package_ui, outdir_ui, default_dir):
        default_dir.mkdir(parents=True, exist_ok=True)
        self.outdir_ui = self._bind_widget(outdir_ui, QgsFileWidget)
        self.package_ui = self._bind_widget(package_ui, QCheckBox)

        self.outdir_ui.setStorageMode(self.outdir_ui.GetDirectory)
        self.outdir_ui.setFilePath(str(default_dir))
        print(f"self.outdir_ui:{self.outdir_ui.filePath()}")
        self.setup_connections()
        
    def setup_connections(self):
        self.package_ui.toggled.connect(self.toggle_fw_editability)

    def toggle_fw_editability(self, checked):
        self.outdir_ui.setEnabled(checked)

    def get_qfield_outdir(self):
        qfield_outdir = Path(self.outdir_ui.filePath())
        if not qfield_outdir.exists():
            QMessageBox.warning(self, "Dossier invalide", "Veuillez choisir un répertoire valide.")
            return
        return qfield_outdir