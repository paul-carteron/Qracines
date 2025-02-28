from PyQt5.QtWidgets import QDialog
from .global_settings_dialog import Ui_GlobalSettingsDialog
from qgis.core import *

# Import from utils folder
from ..utils.variable_utils import VariableUtils

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

    def load_settings(self):
        """Charge les paramètres enregistrés."""
        settings = QgsSettings()
        agence = settings.value("MyCompany/Agency", "")
        user = settings.value("MyCompany/User", "")

        # Sélectionner l'agence si elle existe dans la liste
        if agence in self.agences:
            self.ui.combobox_agence.setCurrentText(agence)
        else:
            self.ui.combobox_agence.setCurrentIndex(-1)  # Aucun choix par défaut

        self.ui.userInput.setText(user)

    def save_settings(self):
        """Enregistre les paramètres."""
        settings = QgsSettings()
        agence = self.ui.combobox_agence.currentText()
        user = self.ui.userInput.text()
        
         # Sauvegarder les paramètres
        settings.setValue("MyCompany/Agency", self.ui.combobox_agence.currentText())
        settings.setValue("MyCompany/User", self.ui.userInput.text())
        
        # Créer et sauvegarder la variable forest_office
        self.set_forest_office(agence)
        
    def set_forest_office(self, agence):
        """Crée et enregistre la variable forest_office en fonction de l'agence sélectionnée."""
        forest_office = ""
        if agence == 'Boulogne':
            forest_office = (
                'Racines\n'
                '39, rue Fessart – 92 100 Boulogne\n'
                '+33 1 46 05 49 63\n'
                'cabinet@racines.com\n'
                'www.racines.com'
            )
        elif agence == 'Nancy':
            forest_office = (
                'Racines\n'
                '23, rue Saint Dizier – 54 000 Nancy\n'
                '+33 3 54 00 16 47\n'
                'cabinet@racines.com\n'
                'www.racines.com'
            )
        elif agence == 'Chaumont':
            forest_office = (
                'Racines\n'
                '5, rue du Château – 52 000 Chamarandes\n'
                '+33 3 25 03 16 97\n'
                'cabinet@racines.com\n'
                'www.racines.com'
            )
        elif agence == 'Le Mans':
            forest_office = (
                'Racines\n'
                '29 rue des Marais Bât C – 72 000 Le Mans\n'
                '+33 2 43 42 82 67\n'
                'cabinet@racines.com\n'
                'www.racines.com'
            )
        elif agence == 'Alluy':
            forest_office = (
                'Racines\n'
                '310, rue des Heurtras – 58 110 Alluy\n'
                '+33 6 08 71 08 51\n'
                'cabinet@racines.com\n'
                'www.racines.com'
            )

        # Enregistrer la variable forest_office dans le projet
        variable_utils = VariableUtils(None)
        variable_utils.set_project_variable('forest_office', forest_office)

    """ def set_project_variable(self, name, value):
        Enregistre une variable dans le projet QGIS.
        QgsProject.instance().setCustomVariables({name: value}) """
