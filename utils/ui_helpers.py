from PyQt5.QtWidgets import QCheckBox, QAbstractItemView, QListWidget, QPushButton, QLineEdit, QMessageBox, QFileDialog

from qgis.core import QgsProject
from qgis.gui import QgsFileWidget
from qgis.utils import iface

from .variable_utils import get_project_variable
from .layer_utils import load_rasters, zoom_on_layer, replier
from .qfield_utils import package_for_qfield

import unicodedata
from pathlib import Path
from typing import Type, Any, List, Iterable, Optional


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
    """Utility class that wires UI elements and calls *package_for_qfield*.

    Parameters
    ----------
    ui
        Top‑level Qt designer‑generated widget.
    package_ui
        Name of a :class:`QCheckBox` indicating whether the user wants the
        project to be packaged for QField.
    outdir_ui
        Name of a :class:`QgsFileWidget` used to pick the output directory.
    default_dir
        Directory suggested to the user; it will be created if necessary.
    """

    def __init__(self, ui, package_ui: str, outdir_ui: str, default_dir: Path):
        self.ui = ui
        self.iface = iface
        self.project = QgsProject.instance()

        # ─── Bind widgets ────────────────────────────────────────────────────
        self.package_ui: QCheckBox = self._bind_widget(package_ui, QCheckBox)
        self.outdir_ui: QgsFileWidget = self._bind_widget(outdir_ui, QgsFileWidget)

        # ─── Default directory ───────────────────────────────────────────────
        self.default_dir = Path(default_dir).expanduser()
        self._ensure_default_dir()

        # ─── Configure *outdir* widget ───────────────────────────────────────
        self.outdir_ui.setStorageMode(self.outdir_ui.GetDirectory)
        self.outdir_ui.setFilePath(str(self.default_dir))
        self.outdir_ui.setEnabled(self.package_ui.isChecked())

        # ─── UI interactions ────────────────────────────────────────────────
        self.package_ui.toggled.connect(self.outdir_ui.setEnabled)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _ensure_default_dir(self) -> None:
        """Create *default_dir* if it does not already exist."""
        try:
            self.default_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self.iface.mainWindow(),"Erreur disque",f"Impossible de créer\n{self.default_dir}:\n{exc}",)
    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    @property
    def outdir(self) -> Path:
        """Return the output directory selected by the user.

        If the widget is empty, fall back to *default_dir*.
        Raises *FileNotFoundError* (and shows a dialog) when the directory
        does not exist.
        """
        path = Path(self.outdir_ui.filePath() or self.default_dir).expanduser()
        if not path.exists():
            QMessageBox.warning(self.iface.mainWindow(), "Dossier invalide", "Veuillez choisir un répertoire valide.",)
            raise FileNotFoundError(path)
        return path

    # ------------------------------------------------------------------
    # Business logic
    # ------------------------------------------------------------------
    def is_valid(self) -> bool:
        """Return *True* when QField packaging is requested."""
        return self.package_ui.isChecked()

    @staticmethod
    def construct_filename(prefix: str, codes: Iterable[str]) -> str:
        """Return the `{prefix}_{forest_prefix}_{codes}` filename.

        *forest_prefix* is taken from the project variable `forest_prefix`.
        """
        forest_prefix = get_project_variable("forest_prefix") or ""
        parts = [prefix, forest_prefix, "_".join(codes)]
        return "_".join(filter(None, parts))

    def package(self, prefix: str, codes: Iterable[str]) -> Optional[Path]:
        """Package the current project for QField and return the archive path.

        If the checkbox is unchecked, the method returns *None* immediately so
        that calling code can keep its existing workflow untouched.
        """
        filename = self.construct_filename(prefix, codes)
        package_for_qfield(self.iface, self.project, self.outdir, filename)
        return self.outdir / filename

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
    
class GpkgLoader(UIBinderMixin):
    def __init__(self, *, ui, add, selected):
        self.ui = ui
        self.add = self._bind_widget(add, QPushButton)
        self.selected = self._bind_widget(selected, QListWidget)

        self.add.clicked.connect(self._on_add)

    def _on_add(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Sélectionner des fichiers à importer", "", "GeoPackage (*.gpkg)")
        if paths:
            self.selected.addItems(paths)

    @property
    def selected_files(self) -> List[str]:
        return  [self.selected.item(i).text() for i in range(self.selected.count())]
    
    def is_valid(self) -> bool:
        """
        Validate that there is at least one selected file,
        that each path exists, and that each has .gpkg extension.
        Returns True if valid, False otherwise (after showing a warning).
        """
        # 1) No files selected
        if not self.selected_files:
            QMessageBox.warning(self, "Aucun fichier", "Aucun GeoPackage sélectionné.")
            return False

        # 2) Check existence
        missing = [f for f in self.selected_files if not Path(f).exists()]
        if missing:
            QMessageBox.warning(
                self,
                "Fichiers introuvables",
                "Les fichiers suivants n'existent pas :\n" + "\n".join(missing)
            )
            return False

        # 3) (Optional) Check extension
        invalid_ext = [f for f in self.selected_files if Path(f).suffix.lower() != ".gpkg"]
        if invalid_ext:
            QMessageBox.warning(
                self,
                "Extension invalide",
                "Les fichiers suivants ne sont pas des .gpkg :\n" + "\n".join(invalid_ext)
            )
            return False

        # All good!
        return True