from pathlib import Path

from qgis.PyQt.QtWidgets import QDialog, QFileDialog, QCompleter
from qgis.core import Qgis, QgsProject
from qgis.utils import iface
from .forest_settings_dialog import Ui_ForestSettingsDialog
from qgis.PyQt.QtCore import Qt

# Import from utils folder
from ...utils.variable_utils import (
    get_project_variable, 
    set_project_variable, 
    get_formated_surface, 
    get_grouped_values_from_shapefile, 
    sum_surface_from_shapefile
    )
from ...utils.path_manager import get_racines_path, get_path

class ForestSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.ui = Ui_ForestSettingsDialog()
        self.ui.setupUi(self)
        
        # Connecter les boutons
        self.ui.buttonBox.accepted.connect(self.save_settings)
        self.ui.pushButton.clicked.connect(self.select_directory)

        # Connection des checkboxes
        self.nom_checkbox = {
            self.ui.checkBox_domaine: "Domaine",
            self.ui.checkBox_massif: "Massif",
            self.ui.checkBox_foret: "Forêt",
            self.ui.checkBox_bois: "Bois",
        }
        for cb in self.nom_checkbox:
            cb.toggled.connect(self.update_forest_name)

        self.ui.pushButton_refresh.clicked.connect(self.fill_in_cartouche)

        # Récupérer les forêts
        self.forest_path_lookup = self.get_forest_path_lookup()
        forest_keys = sorted(self.forest_path_lookup.keys())

        self.setup_forest_combobox(self.ui.forest_path, forest_keys)
        self.ui.forest_path.currentIndexChanged.connect(self.select_directory_from_forest_name)

        # Charger les paramètres existants
        self.load_settings()

    def load_settings(self):
        self.ui.forest_path.setCurrentText(get_project_variable("forest_dirname") or "")
        self.directory = get_project_variable("forest_directory") or ""
        self.ui.lineEdit_prefixe.setText(get_project_variable("forest_prefix") or "")
        self.ui.lineEdit_name.setText(get_project_variable("forest_name") or "")
        self.ui.lineEdit_city.setText(get_project_variable("forest_city") or "")
        self.ui.lineEdit_owner.setText(get_project_variable("forest_owner") or "")
        self.ui.doubleSpinBox_1.setValue(float(get_project_variable("surface_boisee") or 0))
        self.ui.doubleSpinBox_2.setValue(float(get_project_variable("surface_non_boisee") or 0))

    def save_settings(self):
      
        # Récupère les paramètres
        directory = self.directory
        dirname = self.ui.forest_path.currentText()
        prefix = self.ui.lineEdit_prefixe.text()
        name = self.ui.lineEdit_name.text()
        city = self.ui.lineEdit_city.text()
        owner = self.ui.lineEdit_owner.text()
        surface_boisee = self.ui.doubleSpinBox_1.value()
        surface_non_boisee = self.ui.doubleSpinBox_2.value()
        surface_totale = surface_boisee + surface_non_boisee
        formated_surface = get_formated_surface(surface_boisee * 10000, surface_non_boisee * 10000)

        settings = {
            "directory": str(directory),
            "dirname": dirname,
            "prefix": prefix,
            "name": name,
            "city": city,
            "owner": owner,
            "surface_boisee": surface_boisee,
            "surface_non_boisee": surface_non_boisee,
            "surface_totale": surface_totale,
            "formated_surface": formated_surface
        }

        for key, value in settings.items():
            set_project_variable(f"forest_{key}", value)
            
        self.iface.messageBar().pushMessage("Qsequoia2", f"Dossier {dirname} sélectionné avec succès", level=Qgis.Success, duration=10)

    def select_directory(self):

        default_path = get_racines_path("cartographie") / "2_FORETS"
        self.directory = QFileDialog.getExistingDirectory(self, "Sélectionner…", str(default_path))

        if not self.directory:
            return 
          
        self.fill_in_cartouche()
    
    def select_directory_from_forest_name(self):
        forest_name = self.ui.forest_path.currentText()
        if forest_name in self.forest_path_lookup:
            self.directory = self.forest_path_lookup.get(forest_name)

        if not self.directory:
            return 
        
        self.fill_in_cartouche()

    def fill_in_cartouche(self):
        # Compute key paths
        prefix = self._get_prefix_from_directory(self.directory)
        parca_path = get_path("parca_polygon", prefix, self.directory)
        ua_path = get_path("ua_polygon", prefix, self.directory)

        # fill in cartouche
        self._set_directory_and_prefix(self.directory, prefix)
        self._set_name(prefix)
        self._set_city_and_owner(parca_path)
        self._set_surface(ua_path, parca_path)
    
    @staticmethod
    def setup_forest_combobox(combo, forest_keys):
        combo.clear()
        combo.addItems(sorted(forest_keys))
        combo.setEditable(True)
        completer = QCompleter(forest_keys, combo)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        combo.setCompleter(completer)
        combo.setCurrentIndex(-1)

    @staticmethod
    def get_forest_path_lookup():
        # return { dirname: dirpath}
        interne_path = get_racines_path("cartographie") / "2_FORETS"
        externe_path = get_racines_path("cartographie") / "3_EXTERIEUR"
        fdr_path = get_racines_path("cartographie") / "4_FDR"

        return {
            p.name: p for path in [interne_path, externe_path, fdr_path]
            for p in path.glob("*/*" if path == interne_path else "*/")
            if p.is_dir()
        }

    @staticmethod
    def _get_prefix_from_directory(directory):
        """
        Récupère la partie avant le premier '_' dans le nom du dossier.
        Si aucun '_' n'est trouvé, renvoie une chaîne vide.
        """
        name = Path(directory).name
        prefix, sep, suffix = name.partition("_")
        return suffix if sep else prefix

    def _set_directory_and_prefix(self, directory, prefix):
        dirname = Path(directory).name
        path = Path(directory)
        self.ui.forest_path.setCurrentText(dirname)
        set_project_variable("forest_dirname", dirname)
        set_project_variable("forest_directory", path)

        self.ui.lineEdit_prefixe.setText(prefix)
        set_project_variable("forest_prefix", prefix)

    def _set_name(self, prefix):
        self.name = prefix.title() if prefix else ""
        self.ui.lineEdit_name.setText(self.name)
        set_project_variable("forest_name", self.name)

    def _set_city_and_owner(self, parca_path):
        city = owner = ""
        if parca_path.exists():
            city = get_grouped_values_from_shapefile(parca_path, "COM_NOM", "DEP_CODE", "SURF_CA")
            owner = get_grouped_values_from_shapefile(parca_path, "PROP", None, "SURF_CA")

        self.ui.lineEdit_city.setText(city)
        set_project_variable("forest_city", city)

        self.ui.lineEdit_owner.setText(owner)
        set_project_variable("forest_owner", owner)

    def _set_surface(self, ua_path, parca_path):
        surface_boisee = surface_non_boisee = 0
        if ua_path.exists():
            surface_boisee = sum_surface_from_shapefile(ua_path, "SURF_COR", "OCCUP_SOL", "BOISEE")
            surface_non_boisee = sum_surface_from_shapefile(ua_path, "SURF_COR", "OCCUP_SOL", "NON BOISEE") or 0
        else:
            if parca_path.exists():
                surface_boisee = sum_surface_from_shapefile(parca_path, "SURF_CA") or 0
                surface_non_boisee = sum_surface_from_shapefile(parca_path, "SURF_COR", "OCCUP_SOL", "NON BOISEE") or 0

        surface_totale = surface_boisee + surface_non_boisee
        set_project_variable("forest_surface_totale", surface_totale)

        self.ui.doubleSpinBox_1.setValue(surface_boisee)
        set_project_variable("forest_surface_boisee", surface_boisee)

        self.ui.doubleSpinBox_2.setValue(surface_non_boisee)
        set_project_variable("forest_surface_non_boisee", surface_non_boisee)

    def update_forest_name(self):

        base = self.name or get_project_variable("forest_name") or ""

        # find the first‐checked box (if any) and grab its label
        prefix = next((label for cb, label in self.nom_checkbox.items() if cb.isChecked()), "")

        if prefix and base:
            # plural names take " des "
            if base.lower().endswith("s"):
                connector = " des "
            # then vowel or mute-h → d'
            elif base[0].lower() in ("a","e","i","o","u","h"):
                connector = " d'"
            # otherwise normal " de "
            else:
                connector = " de "
            full = f"{prefix}{connector}{base}"
        else:
            full = base
            
        self.ui.lineEdit_name.setText(full)
      
    def save_current_project(self, map_project):
        if self.ui.checkBox_saved.isChecked():
            project = QgsProject.instance()
            save_path = get_path(map_project.lower(), self.name, self.directory)
            project.write(save_path)
