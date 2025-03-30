from PyQt5.QtWidgets import *
from .global_settings_dialog import Ui_GlobalSettingsDialog
from qgis.core import *

# Import from utils folder
from ..utils.variable_utils import *

class GlobalSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_GlobalSettingsDialog()
        self.ui.setupUi(self)
        
        # Liste des agences possibles
        self.agences = ["Boulogne", "Nancy", "Chaumont", "Le Mans", "Alluy"]
        self.ui.combobox_agence.addItems(self.agences)
        
        # Charger les paramètres existants
        self.load_settings()

        # Connecter le bouton OK
        self.ui.buttonBox.accepted.connect(self.save_settings)
        self.ui.stylesButton.clicked.connect(self.select_styles_directory)
        self.ui.modelsButton.clicked.connect(self.select_models_directory)

    def load_settings(self):
        # Agence
        agence = get_global_variable("user_office_name")
        if agence in self.agences:
            self.ui.combobox_agence.setCurrentText(agence) # Sélectionner l'agence si elle existe dans la liste
        else:
            self.ui.combobox_agence.setCurrentIndex(-1)  # Aucun choix par défaut
        
        # Répertoire de styles
        styles_dir = get_project_variable("styles_directory")
        if styles_dir:
            self.ui.stylesInput.setText(styles_dir)
            
        # Répertoire de modèles
        models_dir = get_project_variable("models_directory")
        if styles_dir:
            self.ui.modelsInput.setText(models_dir)
        
        # Utilisateur
        user = get_global_variable("user_full_name")
        self.ui.userInput.setText(user)

    def save_settings(self):
        # Récupère les paramètres
        agence = self.ui.combobox_agence.currentText()
        styles_dir = self.ui.stylesInput.text()
        models_dir = self.ui.modelsInput.text()
        user = self.ui.userInput.text()
        
        # Sauvegarder les paramètres
        set_global_variable("user_office_name", agence)
        set_global_variable("styles_directory", styles_dir)
        set_global_variable("models_directory", models_dir)
        set_global_variable("user_full_name", user)
        
        # Créer et sauvegarder la variable user_office_full_name
        self.set_forest_office(agence)
        
    def set_forest_office(self, agence):
        user_office_full_name = ""
        if agence == 'Boulogne':
            user_office_full_name = (
                'Racines\n'
                '39, rue Fessart – 92 100 Boulogne\n'
                '+33 1 46 05 49 63\n'
                'cabinet@racines.com\n'
                'www.racines.com'
            )
        elif agence == 'Nancy':
            user_office_full_name = (
                'Racines\n'
                '23, rue Saint Dizier – 54 000 Nancy\n'
                '+33 3 54 00 16 47\n'
                'cabinet@racines.com\n'
                'www.racines.com'
            )
        elif agence == 'Chaumont':
            user_office_full_name = (
                'Racines\n'
                '5, rue du Château – 52 000 Chamarandes\n'
                '+33 3 25 03 16 97\n'
                'cabinet@racines.com\n'
                'www.racines.com'
            )
        elif agence == 'Le Mans':
            user_office_full_name = (
                'Racines\n'
                '29 rue des Marais Bât C – 72 000 Le Mans\n'
                '+33 2 43 42 82 67\n'
                'cabinet@racines.com\n'
                'www.racines.com'
            )
        elif agence == 'Alluy':
            user_office_full_name = (
                'Racines\n'
                '310, rue des Heurtras – 58 110 Alluy\n'
                '+33 6 08 71 08 51\n'
                'cabinet@racines.com\n'
                'www.racines.com'
            )
        set_global_variable('user_office_full_name', user_office_full_name)
        
    def select_styles_directory(self):
        UserPath = os.path.expanduser("~")
        StartPath = os.path.join(UserPath, "Racines", "Cartographie - Documents", "1_MODELES")
        dir_path = QFileDialog.getExistingDirectory(self, "Sélectionner le répertoire de travail", StartPath)
        if dir_path:
            self.ui.stylesInput.setText(dir_path)

    def select_models_directory(self):
        UserPath = os.path.expanduser("~")
        StartPath = os.path.join(UserPath, "Racines", "Cartographie - Documents", "1_MODELES")
        dir_path = QFileDialog.getExistingDirectory(self, "Sélectionner le répertoire de travail", StartPath)
        if dir_path:
            self.ui.modelsInput.setText(dir_path)
