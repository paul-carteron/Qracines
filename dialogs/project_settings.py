from PyQt5.QtWidgets import QDialog, QFileDialog
from .project_settings_dialog import Ui_ProjectSettingsDialog
from qgis.core import QgsSettings
import os

class ProjectSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_ProjectSettingsDialog()
        self.ui.setupUi(self)
        
        # Liste des projets possibles
        self.projects = ["SITUATION", "ASSEMBLAGE", "PEUPLEMENTS", "GEOLOGIE", "ENJEUX"]
        self.ui.comboBox_projects.addItems(self.projects)
        
        # Charger les paramètres existants
        self.load_settings()

        # Connecter les boutons
        self.ui.buttonBox.accepted.connect(self.save_settings)
        self.ui.pushButton.clicked.connect(self.select_directory)

    def load_settings(self):
        """Charge les paramètres enregistrés."""
        settings = QgsSettings()
        
        # Charger le répertoire de travail
        work_dir = settings.value("Project/WorkDirectory", "")
        if work_dir:
            self.ui.lineEdit_repertoire.setText(work_dir)

        # Charger le préfixe de la forêt
        forest_prefix = settings.value("Project/ForestPrefix", "")
        self.ui.lineEdit_prefixe.setText(forest_prefix)

        # Charger le projet de carte sélectionné
        map_project = settings.value("Project/MapProject", "")
        if map_project:
            self.ui.comboBox_projects.setCurrentText(map_project)

    def save_settings(self):
        """Enregistre les paramètres."""
        settings = QgsSettings()
        
        # Sauvegarder le répertoire de travail
        settings.setValue("Project/WorkDirectory", self.ui.lineEdit_repertoire.text())
        
        # Sauvegarder le préfixe de la forêt
        settings.setValue("Project/ForestPrefix", self.ui.lineEdit_prefixe.text())
        
        # Sauvegarder le projet de carte sélectionné
        settings.setValue("Project/MapProject", self.ui.comboBox_projects.currentText())

    def select_directory(self):
        """Ouvre une boîte de dialogue pour sélectionner un répertoire."""
        UserPath = os.path.expanduser("~")
        StartPath = os.path.join(UserPath, "Racines", "Cartographie - Documents", "2_FORETS")
        
        dir_path = QFileDialog.getExistingDirectory(self, "Sélectionner le répertoire de travail", StartPath)
        if dir_path:
            self.ui.lineEdit.setText(dir_path)
