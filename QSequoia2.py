# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QAction, QToolButton, QMenu
from PyQt5.QtGui import QIcon

import os

# Import from dialogs folder
from .dialogs.global_settings import *
from .dialogs.project_settings import *
from .dialogs.add_data import *
from .dialogs.diagnostic import *
from .dialogs.pedology import *
from .dialogs.tree_marking import *
from .dialogs.expertise import *

# Import from utils folder
from .utils.variable_utils import *
from .utils.layer_utils import *
from .utils.qfield_utils import *

class QSequoia2:
    def __init__(self, iface):
        self.iface = iface
        self.global_action = None
        self.project_action = None
        self.add_data_action = None
        self.diagnostic_action = None
        self.pedology_action = None
        self.tree_marking_action = None
        self.expertise_action = None
        
        self.toolbar = None
        self.global_dialog = None
        self.project_dialog = None
        self.add_data_dialog = None
        self.diagnostic_dialog = None
        self.pedology_dialog = None
        self.tree_marking_dialog = None
        self.expertise_dialog = None

        self.plugin_name = "QSequoia2"

    def initGui(self):
        # Initialisation
        plugin_dir = os.path.dirname(__file__)
        
        # Toolbar
        if self.toolbar is None:
            self.toolbar = self.iface.addToolBar(self.plugin_name)
            self.toolbar.setObjectName("QSequoia2Toolbar")  # Set a unique object name

        # Global Settings action
        if self.global_action is None:
            global_icon = os.path.join(plugin_dir, "icons", "global_settings.svg")
            self.global_action = QAction(QIcon(global_icon), "Global Settings", self.iface.mainWindow())
            self.global_action.triggered.connect(self.open_global_settings)
            self.toolbar.addAction(self.global_action)
            self.iface.addPluginToMenu(self.plugin_name, self.global_action)
        
        # Project Settings action
        if self.project_action is None:
            project_icon = os.path.join(plugin_dir, "icons", "project_settings.svg")
            self.project_action = QAction(QIcon(project_icon), "Project Settings", self.iface.mainWindow())
            self.project_action.triggered.connect(self.open_project_settings)
            self.toolbar.addAction(self.project_action)
            self.iface.addPluginToMenu(self.plugin_name, self.project_action)
            
        # Add data action
        if self.add_data_action is None:
            project_icon = os.path.join(plugin_dir, "icons", "add_data.svg")
            self.add_data_action = QAction(QIcon(project_icon), "Ajouter des couches", self.iface.mainWindow())
            self.add_data_action.triggered.connect(self.open_add_data)
            self.toolbar.addAction(self.add_data_action)
            self.iface.addPluginToMenu(self.plugin_name, self.add_data_action)
            
        # Add diagnostic action
        if self.diagnostic_action is None:
            project_icon = os.path.join(plugin_dir, "icons", "diagnostic.svg")
            self.diagnostic_action = QAction(QIcon(project_icon), "Diagnostic", self.iface.mainWindow())
            self.diagnostic_action.triggered.connect(self.open_diagnostic)
            self.toolbar.addAction(self.diagnostic_action)
            self.iface.addPluginToMenu(self.plugin_name, self.diagnostic_action)
            
        # Add pedology action
        if self.pedology_action is None:
            project_icon = os.path.join(plugin_dir, "icons", "pedology.svg")
            self.pedology_action = QAction(QIcon(project_icon), "Pedologie", self.iface.mainWindow())
            self.pedology_action.triggered.connect(self.open_pedology)
            self.toolbar.addAction(self.pedology_action)
            self.iface.addPluginToMenu(self.plugin_name, self.pedology_action)
        
        # Add tree_marking action
        if self.tree_marking_action is None:
            project_icon = os.path.join(plugin_dir, "icons", "tree_marking.svg")
            self.tree_marking_action = QAction(QIcon(project_icon), "Martelage", self.iface.mainWindow())
            self.tree_marking_action.triggered.connect(self.open_tree_marking)
            self.toolbar.addAction(self.tree_marking_action)
            self.iface.addPluginToMenu(self.plugin_name, self.tree_marking_action)

        # Add expertise dropdown button
        expertise_icon = os.path.join(plugin_dir, "icons", "expertise.svg")
        expertise_button = QToolButton()
        expertise_button.setIcon(QIcon(expertise_icon))
        expertise_button.setToolTip("Expertise")
        expertise_button.setPopupMode(QToolButton.InstantPopup)

        # Create menu for expertise
        menu = QMenu()
        menu.addAction("Créer une expertise", self.open_expertise_create)
        menu.addAction("Importer une expertise", self.open_expertise_import)
        expertise_button.setMenu(menu)

        # Add to toolbar
        self.toolbar.addWidget(expertise_button)

    def open_global_settings(self):
        if not self.global_dialog:
            self.global_dialog = GlobalSettingsDialog()
        self.global_dialog.exec_()

    def open_project_settings(self):
        if not self.project_dialog:
            self.project_dialog = ProjectSettingsDialog()
        self.project_dialog.exec_()
        
    def open_add_data(self):
        if not self.add_data_dialog:
            self.add_data_dialog = AddDataDialog()
        self.add_data_dialog.exec_()
        
    def open_diagnostic(self):
        if not self.diagnostic_dialog:
            self.diagnostic_dialog = DiagnosticDialog()
        self.diagnostic_dialog.exec_()
        
    def open_pedology(self):
        if not self.pedology_dialog:
            self.pedology_dialog = PedologyDialog()
        self.pedology_dialog.exec_()
        
    def open_tree_marking(self):
        if not self.tree_marking_dialog:
            self.tree_marking_dialog = Tree_markingDialog()
        self.tree_marking_dialog.exec_()
        
    def open_expertise_import(self):
        dialog = ExpertiseDialog(mode="import")
        dialog.exec_()

    def open_expertise_create(self):
        forest = get_project_variable("forest_prefix")
        if not forest:
            QMessageBox.warning(iface.mainWindow(), "Forêt non sélectionnée","Veuillez sélectionner une forêt avant de lancer l'expertise.")
            return
        dialog = ExpertiseDialog(mode="create")
        dialog.exec_()

    def unload(self):
        
        # Remove menu actions on unload
        if self.global_action:
            self.iface.removePluginMenu(self.plugin_name, self.global_action)
            self.toolbar.removeAction(self.global_action)
            self.global_action.deleteLater()  # Ensure the action is deleted
            self.global_action = None

        if self.project_action:
            self.iface.removePluginMenu(self.plugin_name, self.project_action)
            self.toolbar.removeAction(self.project_action)
            self.project_action.deleteLater()  # Ensure the action is deleted
            self.project_action = None
            
        if self.add_data_action:
            self.iface.removePluginMenu(self.plugin_name, self.add_data_action)
            self.toolbar.removeAction(self.add_data_action)
            self.add_data_action.deleteLater()  # Ensure the action is deleted
            self.add_data_action = None
            
        if self.diagnostic_action:
            self.iface.removePluginMenu(self.plugin_name, self.diagnostic_action)
            self.toolbar.removeAction(self.diagnostic_action)
            self.diagnostic_action.deleteLater()  # Ensure the action is deleted
            self.diagnostic_action = None
          
        if self.pedology_action:
            self.iface.removePluginMenu(self.plugin_name, self.pedology_action)
            self.toolbar.removeAction(self.pedology_action)
            self.pedology_action.deleteLater()  # Ensure the action is deleted
            self.pedology_action = None
            
        if self.tree_marking_action:
            self.iface.removePluginMenu(self.plugin_name, self.tree_marking_action)
            self.toolbar.removeAction(self.tree_marking_action)
            self.tree_marking_action.deleteLater()  # Ensure the action is deleted
            self.tree_marking_action = None

        if self.expertise_action:
            self.iface.removePluginMenu(self.plugin_name, self.expertise_action)
            self.toolbar.removeAction(self.expertise_action)
            self.expertise_action.deleteLater()  # Ensure the action is deleted
            self.expertise_action = None

        # Remove the toolbar if it exists
        if self.toolbar:
            self.toolbar.deleteLater()  # Properly remove the toolbar
            self.toolbar = None
