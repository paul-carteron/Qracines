from qgis.PyQt.QtWidgets import QDialog
from qgis.core import Qgis, QgsProject
from qgis.utils import iface
from .project_settings_dialog import Ui_ProjectSettingsDialog

# Import from utils folder
from ..utils.variable_utils import get_project_variable, set_project_variable, clear_project
from ..utils.path_manager import get_project, get_path
from ..utils.layer_utils import create_map_project, configure_snapping

class ProjectSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.ui = Ui_ProjectSettingsDialog()
        self.ui.setupUi(self)

        # Liste des projets possibles
        self.projects = get_project()

        cb = self.ui.comboBox_projects
        cb.addItem("") 
        cb.addItems(self.projects.values())
        cb.setCurrentIndex(0)
        
        # Connecter les boutons
        self.ui.buttonBox.accepted.connect(self.save_settings)

    def save_settings(self):
      
        # Récupère le projet
        selected_project_name = self.ui.comboBox_projects.currentText()
        project_key = next((key for key, name in self.projects.items() if name == selected_project_name), None)

        if project_key in self.projects:
            type_project = "wooded" if get_project_variable("forest_surface_non_boisee") < 0 else "unwooded"
            set_project_variable("forest_map_project", project_key)
            set_project_variable("forest_type_project", type_project)

        # Lance la création de la map
        clear_project()

        if project_key in self.projects:
            create_map_project(project_key.lower(), type_project)
            configure_snapping()
            self.iface.messageBar().pushMessage("Qsequoia2", f"Projet {project_key} généré avec succès", level=Qgis.Success, duration=10)
        
        # Save project qgz
        if self.ui.checkBox_saved.isChecked():
            project = QgsProject.instance()
            save_path = get_path(project_key)
            project.write(str(save_path))
