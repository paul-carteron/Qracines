from pathlib import Path

from qgis.PyQt.QtWidgets import QDialog
from qgis.core import Qgis, QgsProject
from qgis.utils import iface
from .project_settings_dialog import Ui_ProjectSettingsDialog

# Import from utils folder
from ...utils.variable_utils import get_project_variable, set_project_variable, get_global_variable, clear_project
from ...utils.path_manager import get_project, get_path, get_default, get_project_default
from ...utils.layer_utils import create_project, configure_snapping 
from ...utils.layout_utils import compute_map_info, import_layout_from_template, configure_layout
from ...utils.utils import show_message

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
        map_project = next((key for key, name in self.projects.items() if name == selected_project_name), None)

        if map_project in self.projects:
            # Récupère le type_project (should be done when in forest_settings)
            type_project = "unwooded" if float(get_project_variable("forest_surface_non_boisee")) > 0 else "wooded"
            set_project_variable("forest_map_project", map_project)
            set_project_variable("forest_type_project", type_project)
            
            # Supprime le projet actuel
            clear_project()

            # Crée le projet ciblé
            create_project(map_project)
            show_message(self.iface, f"Projet {map_project} généré avec succès", "success", 15)
            
            # Configure l'accrochage
            configure_snapping()
            
            # Importe le modèle qpt du composeur
            default = get_project_default(map_project)
            info = compute_map_info(default["info_layer"], default["scale"])
            print(info)

            format = info.get("format_papier")
            orientation = info.get("orientation", "portrait")

            layout = import_layout_from_template(format, orientation)
            print(layout)

            # Configure le composeur
            if layout:
                configure_layout(layout, map_project)
                iface.openLayoutDesigner(layout)
            
            # Save project qgz
            if self.ui.checkBox_saved.isChecked():
                project = QgsProject.instance()
                save_path = get_path(map_project)
                project.write(str(save_path))
