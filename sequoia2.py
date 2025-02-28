# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtSvg import QSvgRenderer
import os

# Import from dialogs folder
from .dialogs.global_settings import GlobalSettingsDialog
from .dialogs.project_settings import ProjectSettingsDialog
from .dialogs.add_data import AddDataDialog
from .dialogs.diagnostic import DiagnosticDialog

# Import from utils folder
from .utils.layer_utils import LayerUtils
from .utils.database_utils import DatabaseUtils
from .utils.variable_utils import VariableUtils

class sequoia2:
    def __init__(self, iface):
        self.iface = iface
        self.global_action = None
        self.project_action = None
        self.add_data_action = None
        self.diagnostic_action = None
        
        self.toolbar = None
        self.global_dialog = None
        self.project_dialog = None
        self.add_data_dialog = None
        self.diagnostic_dialog = None

    def initGui(self):
        # Initialisation
        plugin_dir = os.path.dirname(__file__)
        
        # Toolbar
        if self.toolbar is None:
            self.toolbar = self.iface.addToolBar("Sequoia2")
            self.toolbar.setObjectName("Sequoia2Toolbar")  # Set a unique object name

        # Global Settings action
        if self.global_action is None:
            global_icon = os.path.join(plugin_dir, "icons", "global_settings.svg")
            self.global_action = QAction(QIcon(global_icon), "Global Settings", self.iface.mainWindow())
            self.global_action.triggered.connect(self.open_global_settings)
            self.toolbar.addAction(self.global_action)
            self.iface.addPluginToMenu("Sequoia2", self.global_action)
        
        # Project Settings action
        if self.project_action is None:
            project_icon = os.path.join(plugin_dir, "icons", "project_settings.svg")
            self.project_action = QAction(QIcon(project_icon), "Project Settings", self.iface.mainWindow())
            self.project_action.triggered.connect(self.open_project_settings)
            self.toolbar.addAction(self.project_action)
            self.iface.addPluginToMenu("Sequoia2", self.project_action)
            
        # Add data action
        if self.add_data_action is None:
            project_icon = os.path.join(plugin_dir, "icons", "add_data.svg")
            self.add_data_action = QAction(QIcon(project_icon), "Ajouter des couches", self.iface.mainWindow())
            self.add_data_action.triggered.connect(self.open_add_data)
            self.toolbar.addAction(self.add_data_action)
            self.iface.addPluginToMenu("Sequoia2", self.add_data_action)
            
        # Add diagnostic action
        if self.diagnostic_action is None:
            project_icon = os.path.join(plugin_dir, "icons", "diagnostic.svg")
            self.diagnostic_action = QAction(QIcon(project_icon), "Diagnostic", self.iface.mainWindow())
            self.diagnostic_action.triggered.connect(self.open_diagnostic)
            self.toolbar.addAction(self.diagnostic_action)
            self.iface.addPluginToMenu("Sequoia2", self.diagnostic_action)

    def open_global_settings(self):
        # Show global settings window
        if not self.global_dialog:
            self.global_dialog = GlobalSettingsDialog()
        self.global_dialog.exec_()

    def open_project_settings(self):
        # Show project settings window
        if not self.project_dialog:
            self.project_dialog = ProjectSettingsDialog()
        self.project_dialog.exec_()
        
    def open_add_data(self):
        # Show add data window
        if not self.add_data_dialog:
            self.add_data_dialog = AddDataDialog()
        self.add_data_dialog.exec_()
        
    def open_diagnostic(self):
        # Show add data window
        if not self.diagnostic_dialog:
            self.diagnostic_dialog = DiagnosticDialog()
        self.diagnostic_dialog.exec_()

    def unload(self):
        # Remove menu actions on unload
        if self.global_action:
            self.iface.removePluginMenu("Sequoia2", self.global_action)
            self.toolbar.removeAction(self.global_action)
            self.global_action.deleteLater()  # Ensure the action is deleted
            self.global_action = None

        if self.project_action:
            self.iface.removePluginMenu("Sequoia2", self.project_action)
            self.toolbar.removeAction(self.project_action)
            self.project_action.deleteLater()  # Ensure the action is deleted
            self.project_action = None
            
        if self.add_data_action:
            self.iface.removePluginMenu("Sequoia2", self.add_data_action)
            self.toolbar.removeAction(self.add_data_action)
            self.add_data_action.deleteLater()  # Ensure the action is deleted
            self.add_data_action = None
            
        if self.diagnostic_action:
            self.iface.removePluginMenu("Sequoia2", self.diagnostic_action)
            self.toolbar.removeAction(self.diagnostic_action)
            self.diagnostic_action.deleteLater()  # Ensure the action is deleted
            self.diagnostic_action = None

        # Remove the toolbar if it exists
        if self.toolbar:
            self.toolbar.deleteLater()  # Properly remove the toolbar
            self.toolbar = None

        # Clean up dialogs
        if self.global_dialog:
            self.global_dialog.deleteLater()
            self.global_dialog = None

        if self.project_dialog:
            self.project_dialog.deleteLater()
            self.project_dialog = None
