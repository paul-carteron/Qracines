from pathlib import Path

from qgis.PyQt.QtWidgets import QDialog, QFileDialog
from qgis.core import Qgis, QgsProject
from qgis.utils import iface
from .project_settings_dialog import Ui_ProjectSettingsDialog

# Import from utils folder
from ..utils.variable_utils import (
    get_project_variable, 
    set_project_variable, 
    get_formated_surface, 
    get_grouped_values_from_shapefile, 
    sum_surface_from_shapefile,
    clear_project,
    )
from ..utils.layer_utils import load_wms, load_vectors, zoom_on_layer, create_map_theme, replier, create_map_project
from ..utils.path_manager import get_racines_path, get_path, get_wms, get_config_path

class ProjectSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.ui = Ui_ProjectSettingsDialog()
        self.ui.setupUi(self)

        # Liste des projets possibles
        projects = ["SITUATION", "ASSEMBLAGE", "PEUPLEMENTS", "GEOLOGIE", "ENJEUX"]

        cb = self.ui.comboBox_projects
        cb.addItem("") 
        cb.addItems(projects)
        cb.setCurrentIndex(0)
        
        # Charger les paramètres existants
        self.load_settings()

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

    def load_settings(self):
        self.ui.lineEdit_directory.setText(get_project_variable("forest_directory") or "")
        self.ui.lineEdit_prefixe.setText(get_project_variable("forest_prefix") or "")
        self.ui.lineEdit_name.setText(get_project_variable("forest_name") or "")
        self.ui.lineEdit_city.setText(get_project_variable("forest_city") or "")
        self.ui.lineEdit_owner.setText(get_project_variable("forest_owner") or "")
        self.ui.doubleSpinBox_1.setValue(float(get_project_variable("forest_wooded_surface") or 0))
        self.ui.doubleSpinBox_2.setValue(float(get_project_variable("forest_unwooded_surface") or 0))
        self.ui.comboBox_projects.setCurrentText(get_project_variable("forest_map_project") or "")

    def save_settings(self):
      
        # Récupère les paramètres
        directory = self.ui.lineEdit_directory.text()
        prefix = self.ui.lineEdit_prefixe.text()
        name = self.ui.lineEdit_name.text()
        city = self.ui.lineEdit_city.text()
        owner = self.ui.lineEdit_owner.text()
        surface_boisee = self.ui.doubleSpinBox_1.value()
        surface_non_boisee = self.ui.doubleSpinBox_2.value()
        surface_totale = surface_boisee+surface_non_boisee
        formated_surface = get_formated_surface(surface_boisee * 10000, surface_non_boisee * 10000)
        map_project = self.ui.comboBox_projects.currentText()
        
        if surface_non_boisee >0:
            type_project = "unwooded"
        else:
            type_project = "wooded"
       
        # Sauvegarder les paramètres
        set_project_variable("forest_directory", directory)
        set_project_variable("forest_prefix", prefix)
        set_project_variable("forest_name", name)
        set_project_variable("forest_city", city)
        set_project_variable("forest_owner", owner)
        set_project_variable("forest_map_project", map_project)
        set_project_variable("forest_wooded_surface", surface_boisee)
        set_project_variable("forest_unwooded_surface", surface_non_boisee)
        set_project_variable("forest_surface", surface_totale)
        set_project_variable("forest_formated_surface", formated_surface)
        set_project_variable("forest_type_project", type_project)

        # Lance la création de la map
        self.create_map_project(map_project, type_project)
        self.save_current_project(map_project)

    def select_directory(self):
        # directory is the path to "123456_FORET"
        default_path = get_racines_path("cartographie") / "2_FORETS"
        self.directory = QFileDialog.getExistingDirectory(self, "Sélectionner…", str(default_path))
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
    def _get_prefix_from_directory(path):
        """
        Récupère la partie avant le premier '_' dans le nom du dossier.
        Si aucun '_' n'est trouvé, renvoie une chaîne vide.
        """
        name = Path(path).name
        prefix, sep, suffix = name.partition("_")
        return suffix if sep else prefix


    def _set_directory_and_prefix(self, directory, prefix):
        self.ui.lineEdit_directory.setText(directory)
        set_project_variable("forest_directory", directory)

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
            surface_non_boisee = sum_surface_from_shapefile(ua_path, "SURF_COR", "OCCUP_SOL", "NON BOISEE")
            if not surface_non_boisee:
                surface_non_boisee = 0
              
        else:
            surface_boisee = sum_surface_from_shapefile(parca_path, "SURF_CA")
            surface_non_boisee = 0
        
        self.ui.doubleSpinBox_1.setValue(surface_boisee)
        set_project_variable("forest_wooded_surface", surface_boisee)
        
        self.ui.doubleSpinBox_2.setValue(surface_non_boisee)
        set_project_variable("forest_unwooded_surface", surface_non_boisee)
        
        surface_totale = surface_boisee+surface_non_boisee
        set_project_variable("forest_surface", surface_totale)

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
            
    def create_map_project(self, map_project, type_project):

        clear_project()
        create_map_project(map_project.lower(), type_project)
        self.iface.messageBar().pushMessage("QSequoia2", f"Projet {map_project} généré avec succès", level=Qgis.Success, duration=10)
