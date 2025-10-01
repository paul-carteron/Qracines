from qgis.PyQt.QtWidgets import QDialog, QMessageBox
from qgis.core import QgsProject
from .project_settings_dialog import Ui_ProjectSettingsDialog
from .project_settings_service import compute_layout_info, import_layout, configure_layout

# Import from utils folder
from ...utils.config import get_project, get_path, get_project_canvas, get_project_layout
from ...utils.layers import configure_snapping 
from ...utils.utils import show_message, clear_project, create_project
from ...utils.variable import set_project_variable

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

        # Connect composeur chekbox to occup percentage
        self.ui.cb_composeur.toggled.connect(self.ui.dsb_occup.setEnabled)

    def _get_project_key(self):
        selected_project_name = self.ui.comboBox_projects.currentText()
        project_key = next((key for key, name in self.projects_list.items() if name == selected_project_name), None)
        return project_key
    
    def accept(self):
        project_key = self._get_project_key()
        if not project_key:
            show_message(self.iface, f"Projet {project_key} n'existe pas", "critical", 15)
            return 

        try:
            set_project_variable("forest_map_project", project_key) #why do i need that ? I think is because of composer but i'm not sure anymore
            clear_project()
            create_project(project_key)
            configure_snapping()
            
            show_message(self.iface, f"Projet {project_key} généré avec succès", "success", 15)
            
            canvas_cfg = get_project_canvas(project_key)
            layout_cfg = get_project_layout(project_key)

            if self.ui.cb_composeur.isChecked():
                # Create layout
                # "parca_polygon" is used inside compute_layout_info considering all project should have downloaded parca
                info = compute_layout_info(scale = canvas_cfg.scale, coeff_cadre = self.ui.dsb_occup.value()/100)
                layout = import_layout(self.project, info.paper_format, info.orientation)
                
                # configure layout
                if layout:
                    configure_layout(self.project, self.iface, layout, layout_cfg.theme, canvas_cfg.scale, layout_cfg.legends)
                    self.iface.openLayoutDesigner(layout)
                    
            # Save project qgz
            if self.ui.cb_save_project.isChecked():
                save_path = get_path(project_key)
                self.project.write(str(save_path))

            super().accept()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue :\n{e}")