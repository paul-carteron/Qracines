from pathlib import Path

from qgis.PyQt.QtWidgets import QDialog, QFileDialog, QCompleter
from qgis.core import Qgis, QgsProject
from qgis.utils import iface
from .project_settings_dialog import Ui_ProjectSettingsDialog
from qgis.PyQt.QtCore import Qt

# Import from utils folder
from ..utils.variable_utils import (
    get_project_variable,
    set_project_variable,
    clear_project
    )
from ..utils.layer_utils import load_wms, load_vectors, zoom_on_layer, create_map_theme, replier, create_map_project
from ..utils.path_manager import get_wms, get_config_path, get_logical_files_from, get_path

class ProjectSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.ui = Ui_ProjectSettingsDialog()
        self.ui.setupUi(self)

        # Liste des projets possibles
        output_files = get_logical_files_from("output_folder")
        self.projects = list(output_files.keys())

        cb = self.ui.comboBox_projects
        cb.addItem("") 
        cb.addItems(self.projects)
        cb.setCurrentIndex(0)
        
        # Connecter les boutons
        self.ui.buttonBox.accepted.connect(self.save_settings)

    def save_settings(self):
      
        # Liste des noms de variables à récupérer
        keys = [ 
           "directory", "dirname", "prefix", "name", "city", "owner",
           "surface_boisee", "surface_non_boisee", "surface_totale", "formated_surface"
        ]
        
        # Dictionnaire où seront stockées les valeurs récupérées
        settings = {}
        
        # Récupération des variables
        for key in keys:
            settings[key] = get_project_variable(f"forest_{key}")
      
        # Récupère le projet
        map_project = self.ui.comboBox_projects.currentText()
        
        if map_project in self.projects:
            type_project = "wooded" if settings["surface_non_boisee"] < 0 else "unwooded"
            set_project_variable("forest_map_project", map_project)
            set_project_variable("forest_type_project", type_project)
        else:
            type_project = ""

        # Lance la création de la map
        clear_project()
        if map_project in self.projects:
            create_map_project(map_project.lower(), type_project)
            self.iface.messageBar().pushMessage("Qsequoia2", f"Projet {map_project} généré avec succès", level=Qgis.Success, duration=10)
        
        # Save project qgz
        if self.ui.checkBox_saved.isChecked():
            project = QgsProject.instance()
            save_path = get_path(map_project)
            project.write(str(save_path))
