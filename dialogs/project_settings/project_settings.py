from pathlib import Path

from qgis.PyQt.QtWidgets import QDialog, QMessageBox, QApplication
from qgis.PyQt.QtCore import QEventLoop  
from qgis.core import QgsProject
from .project_settings_dialog import Ui_ProjectSettingsDialog
from .project_settings_service import compute_layout_info, import_layout, configure_layout, _get_layer

# Import from utils folder
from ...utils.variable_utils import get_project_variable, set_project_variable, clear_project
from ...utils.path_manager import get_project, get_path, get_project_default, get_project_legends
from ...utils.layer_utils import create_project, configure_snapping 
from ...utils.utils import show_message


class ProjectSettingsDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.project = QgsProject.instance()
        self.ui = Ui_ProjectSettingsDialog()
        self.ui.setupUi(self)

        # Liste des projets possibles
        self.projects_list = get_project()
       
        cb = self.ui.comboBox_projects
        cb.addItem("") 
        cb.addItems(self.projects_list.values())
        cb.setCurrentIndex(0)

    def _get_project_key(self):
        selected_project_name = self.ui.comboBox_projects.currentText()
        project_key = next((key for key, name in self.projects_list.items() if name == selected_project_name), None)
        return project_key
    
    def _create_project(self, project_key):

        manager = self.project.layoutManager()
        for old in list(manager.layouts()):
            manager.removeLayout(old)

        clear_project()

        create_project(project_key)
        show_message(self.iface, f"Projet {project_key} généré avec succès", "success", 15)
        
        # Configure l'accrochage
        configure_snapping()

        return None
    
    def accept(self):
        project_key = self._get_project_key()
        if not project_key:
            show_message(self.iface, f"Projet {project_key} n'existe pas", "critical", 15)
            return 

        try:
            self._create_project(project_key)
            default = get_project_default(project_key)

            # create layout
            info_layer = _get_layer(self.project, default.info_layer)
            info = compute_layout_info(info_layer, default.scale, buffer_distance = 15)
            layout = import_layout(self.project, info.paper_format, info.orientation)
            
            # configure layout
            legends = get_project_legends(project_key)
            if layout:
                configure_layout(self.project, self.iface, layout, default.composer_theme, default.scale, legends)
                self.iface.openLayoutDesigner(layout)
                
            # Save project qgz
            if self.ui.checkBox_saved.isChecked():
                save_path = get_path(project_key)
                self.project.write(str(save_path))

            super().accept()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue :\n{e}")