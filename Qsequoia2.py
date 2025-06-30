# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QAction, QToolButton, QMenu
from PyQt5.QtGui import QIcon

# Import from dialogs folder
from .dialogs.global_settings import *
from .dialogs.project_settings import *
from .dialogs.add_data import *
from .dialogs.diagnostic import *
from .dialogs.pedology import *
from .dialogs.tree_marking import *
from .dialogs.expertise_import.expertise_import import ExpertiseImportDialog
from .dialogs.expertise_create.expertise_create import ExpertiseCreateDialog

# Import from utils folder
from .utils.variable_utils import *
from .utils.layer_utils import *
from .utils.qfield_utils import *

from pathlib import Path

CLASSIC_BUTTONS = [
#   ("icon-file",            "tooltip",              "handler"              ),
    ("global_settings.svg",  "Global Settings",      "open_global_settings" ),
    ("project_settings.svg", "Project Settings",     "open_project_settings"),
    ("add_data.svg",         "Ajouter des couches",  "open_add_data"        ),
]

QFIELD_BUTTONS = [
#   ("icon-file",        "tooltip",    "create_handler",           "import_handler"          ),
    ("diagnostic.svg",   "Diagnostic", "open_diagnostic_create",   "open_diagnostic_import"  ),
    ("pedology.svg",     "Pédologie",  "open_pedology_create",     "open_pedology_import"    ),
    ("tree_marking.svg", "Martelage",  "open_tree_marking_create", "open_tree_marking_import"),
    ("expertise.svg",    "Expertise",  "open_expertise_create",    "open_expertise_import"   ),
]

class ClassicButton:
    def __init__(self, icon: Path, tooltip: str, slot: callable, iface, plugin_name: str):
        self.plugin_name = plugin_name
        self.iface = iface
        self.action = QAction(QIcon(str(icon)), tooltip, iface.mainWindow())
        self.action.triggered.connect(slot)

    def add_to_toolbar(self, toolbar):
        toolbar.addAction(self.action)
        self.iface.addPluginToMenu(self.plugin_name, self.action)

    def unload(self, toolbar):
        self.iface.removePluginMenu(self.plugin_name, self.action)
        toolbar.removeAction(self.action)
        self.action.deleteLater() 

class QfieldButton:
    def __init__(self, icon: Path, tooltip: str, menu_items: list[tuple[str, callable]]):
        self.button = QToolButton()
        self.button.setIcon(QIcon(str(icon)))
        self.button.setToolTip(tooltip)
        self.button.setPopupMode(QToolButton.InstantPopup)
        self._widget_action = None

        menu = QMenu()
        for label, slot in menu_items:
            menu.addAction(label, slot)
        self.button.setMenu(menu)

    def add_to_toolbar(self, toolbar):
        self._widget_action = toolbar.addWidget(self.button)

    def unload(self, toolbar):
        if self._widget_action is not None:
            toolbar.removeAction(self._widget_action)
        self.button.deleteLater() 

class Qsequoia2:
    def __init__(self, iface):
        self.iface = iface

        self.plugin_dir = Path(__file__).parent
        self.plugin_name = "Qsequoia2"

        self.toolbar = None
        self.buttons = []

        # Classic dialogs
        self.global_dialog = None
        self.project_dialog = None
        self.add_data_dialog = None

        # QField dialogs
        self.diagnostic_create = None
        self.diagnostic_import = None
        self.pedology_create = None
        self.pedology_import = None
        self.tree_marking_create = None
        self.tree_marking_import = None
        self.expertise_create = None
        self.expertise_import = None

    def initGui(self):
        # initGui() is called by QGIS when the plugin is enabled in the UI
        # initGui() is specifically meant to register GUI elements (toolbars, menus, buttons, etc.).

        # Toolbar
        self.toolbar = self.iface.addToolBar(self.plugin_name)
        self.toolbar.setObjectName("Qsequoia2Toolbar")

        for icon, tooltip, handler in CLASSIC_BUTTONS:
            btn = ClassicButton(
                icon = self.plugin_dir / "icons" / icon,
                tooltip = tooltip,
                slot = getattr(self, handler),
                iface = self.iface,
                plugin_name = self.plugin_name
            )
            self.buttons.append(btn)

        for icon, tooltip, create_handler, import_handler in QFIELD_BUTTONS:
            btn = QfieldButton(
                icon = self.plugin_dir / "icons" / icon,
                tooltip = tooltip,
                menu_items = [
                    ("Créer",    getattr(self, create_handler)),
                    ("Importer", getattr(self, import_handler)),
                ]
            )
            self.buttons.append(btn)

        for btn in self.buttons:
            btn.add_to_toolbar(self.toolbar)
            
    # region HANDLERS
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
    
    # DIAGNOSTIC
    def open_diagnostic_create(self):
        if not self.diagnostic_create:
            self.diagnostic_create = DiagnosticDialog()
        self.diagnostic_create.exec_()

    def open_diagnostic_import(self):
        return
        
    # PEDOLOGY
    def open_pedology_create(self):
        if not self.pedology_create:
            self.pedology_create = PedologyDialog()
        self.pedology_create.exec_()

    def open_pedology_import(self):
        return
    
    # TREE MARKING
    def open_tree_marking_create(self):
        if not self.tree_marking_create:
            self.tree_marking_create = Tree_markingDialog()
        self.tree_marking_create.exec_()

    def open_tree_marking_import(self):
        return
    
    # EXPERTISE
    def open_expertise_create(self):
        if not self._check_forest_is_selected():
            return None
        
        if not self.expertise_create:
            self.expertise_create = ExpertiseCreateDialog()
        self.expertise_create.exec_()
        
    def open_expertise_import(self):
        if not self._check_forest_is_selected():
            return None

        if not self.expertise_import:
            self.expertise_import = ExpertiseImportDialog()
        self.expertise_import.exec_()
        
    # endregion
    
    @staticmethod
    def _check_forest_is_selected():
        forest = get_project_variable("forest_prefix")
        if not forest:
            QMessageBox.warning(iface.mainWindow(), "Forêt non sélectionnée","Veuillez sélectionner une forêt avant de lancer l'expertise.")
            return False
        return True
        

        
    def unload(self):
        for btn in self.buttons:
            btn.unload(self.toolbar)

        self.buttons.clear()
        
        # Remove the toolbar if it exists
        if self.toolbar:
            self.toolbar.deleteLater()  # Properly remove the toolbar
            self.toolbar = None
