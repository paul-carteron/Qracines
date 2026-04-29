from PyQt5.QtWidgets import QCheckBox, QAbstractItemView, QListWidget, QPushButton, QLineEdit, QMessageBox, QFileDialog, QDoubleSpinBox, QSpinBox
from qgis.PyQt.QtCore import QCoreApplication, Qt

from qgis.core import QgsProject, QgsSingleSymbolRenderer, QgsMarkerSymbol, QgsVectorLayer
from qgis.gui import QgsFileWidget
from qgis.utils import iface

from .variable import get_project_variable
from .qfield import package_for_qfield
from .utils import fold
from .processing import create_grid
from .message import messageLog

import unicodedata
from pathlib import Path
from typing import Type, Any, List, Iterable, Optional

from qsequoia2.modules.utils.seq_config import seq_read

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

class DendroController(UIBinderMixin):

    def __init__(self, ui, dendro_spinbox):
        self.ui = ui

        # bind widgets
        self.widgets = {
            key: self._bind_widget(attr, QSpinBox)
            for key, attr in dendro_spinbox.items()
        }

    def get_values(self):
        """Return current dendrometric values from UI"""
        return {key: w.value() for key, w in self.widgets.items()}
    
class RasterController(UIBinderMixin):

    def __init__(self, ui, raster_checkbox):
        self.ui  = ui
        self.cbs = {key: self._bind_widget(attr, QCheckBox) for key, attr in raster_checkbox.items()}
        
    def set_checkbox_states(self):
        is_forest_selected = bool(get_project_variable("forest_prefix"))
        if not is_forest_selected:
            # Disable + uncheck all
            for cb in self.cbs.values():
                cb.setChecked(False)
                cb.setEnabled(False)
            return

    def load_selected_rasters(self, seq_dir, group_name = "RASTER"):

        if not seq_dir:
            raise RuntimeError("Pas de forêt sélectionnée, impossible de charger des rasters")
    
        asked_keys = [k for k, cb in self.cbs.items() if cb.isChecked()]
        messageLog(f"[RASTER CONTROLLER] asked_keys: {asked_keys}")
        if not asked_keys:
            return
        
        group = QgsProject.instance().layerTreeRoot().findGroup(group_name)
        if not group:
            group = QgsProject.instance().layerTreeRoot().addGroup(group_name)

        messageLog(f"[RASTER CONTROLLER] group: {group}")
        for key in asked_keys:
            try:
                loaded = seq_read(key, seq_dir=seq_dir, add_to_project=True, group=group)
            except Exception as e:
                continue

        if group:
            for i, node in enumerate(group.children()):
                node.setItemVisibilityChecked(i == 0)

        if loaded:
            canvas = iface.mapCanvas()
            canvas.setExtent(loaded.extent())
            canvas.refresh()

        fold()

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
        self.default_dir = Path(default_dir)
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
        except Exception as exc:
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
        path = Path(self.outdir_ui.filePath() or self.default_dir)
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
    def construct_filename(prefix: str, seq_id = None, codes: Optional[Iterable[str]] = None) -> str:
        """Return a filename like `{prefix}_{forest_prefix}_{code1}_{code2}_...`, skipping any empty segments."""
        parts = [prefix, seq_id] + list(codes or [])
        return "_".join(filter(None, parts))

    def package(self, prefix: str, seq_id = None, codes: Optional[Iterable[str]] = None) -> Optional[Path]:
        """Package the current project for QField and return the archive path or None if disabled."""
        filename = self.construct_filename(prefix, seq_id, codes)

        # ─── 1) Show a modal “please wait” dialog with no buttons ─────────
        busy = QMessageBox(self.iface.mainWindow())
        busy.setWindowTitle("Packaging for QField")
        busy.setText("Please wait while your project is being packaged…")
        busy.setStandardButtons(QMessageBox.NoButton)    # no “OK” or cancel
        busy.setWindowModality(Qt.WindowModal)
        busy.show()
        QCoreApplication.processEvents()                 # force it to paint immediately

        try:
            # ─── 2) Do the actual packaging work ───────────────────────────
            out = package_for_qfield(self.iface, self.project, self.outdir, filename)
        finally:
            busy.accept()                    # mark as done (closes the dialog)
            busy.deleteLater()               # schedule for deletion
            QCoreApplication.processEvents()

        return out

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
        Fill the 'choices' QListWidget from self.essences.
        Expects self.essences.getFeatures() to yield features
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
            self.add, "Sélectionner des fichiers à importer", "", "GeoPackage (*.gpkg)")
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
    
class GridController(UIBinderMixin):
    def __init__(self, ui, create_grid_ui, points_per_ha_ui):
        self.ui = ui
        self.create_grid_ui = self._bind_widget(create_grid_ui, QCheckBox)
        self.points_per_ha = self._bind_widget(points_per_ha_ui, QDoubleSpinBox)

        # ─── UI interactions ────────────────────────────────────────────────
        self.create_grid_ui.toggled.connect(self.points_per_ha.setEnabled)

    def is_valid(self) -> bool:
        """Return *True* when QField packaging is requested."""
        enabled = self.create_grid_ui.isChecked()
        if not enabled:
            return False
    
        if float(self.points_per_ha.value()) <= 0:
            QMessageBox.warning(self.ui, "Valeur invalide", "Veuillez entrer une valeur positive pour le nombre de points par hectare.")
            return False
        return True

    def create_grid(self, seq_dir):
        
        parca = seq_read("parca", seq_dir=seq_dir, add_to_project=False)
        
        self.name = f"Grille ({self.points_per_ha.value()} pts/ha)"
        grid = create_grid(parca, name = self.name, points_per_ha=float(self.points_per_ha.value()))
        grid = self.style_grid(grid)

        return grid
    
    @staticmethod
    def style_grid(grid: QgsVectorLayer) -> None: 
        sym = QgsMarkerSymbol.createSimple({
            'name': 'cross',
            'size': '3',
            'color': 'transparent',         # fill color (none)
            'outline_color': '#ff5400',     # line color of the cross
            'outline_width': '0.8',         # line thickness
        })
        sym.setOpacity(0.9)
        grid.setRenderer(QgsSingleSymbolRenderer(sym))
        grid.triggerRepaint()

        return grid