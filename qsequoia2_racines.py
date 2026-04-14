from qgis.PyQt.QtWidgets import QMessageBox, QAction, QToolButton, QMenu
from qgis.PyQt.QtGui import QIcon

from .modules.add_data.add_data import AddDataDialog

from .modules.diagnostic.create.diagnostic_create import DiagnosticCreateDialog
from .modules.diagnostic.merge.diagnostic_merge import DiagnosticMergeDialog
from .modules.diagnostic.load.diagnostic_load import DiagnosticLoad

from .modules.expertise.create.expertise_create import ExpertiseCreateDialog
from .modules.expertise.merge.expertise_merge import ExpertiseMergeDialog
from .modules.expertise.load.expertise_load import ExpertiseLoad

from .modules.forest_settings.forest_settings import ForestSettingsDialog

from .modules.global_settings.global_settings import GlobalSettingsDialog

from .modules.pedology.pedology_create import PedologyCreateDialog

from .modules.project_settings.project_settings import ProjectSettingsDialog

from .modules.tree_marking.create.tree_marking_create import TreeMarkingCreateDialog
from .modules.tree_marking.merge.tree_marking_merge import TreeMarkingMergeDialog
from .modules.tree_marking.load.tree_marking_load import TreeMarkingLoad

# import utils
from .utils.variable import get_project_variable, get_global_variable

from pathlib import Path

CLASSIC_BUTTONS = [
#   ("icon-file",            "tooltip",              "handler"              ),
    ("global_settings.svg",  "Global Settings",      "open_global_settings" ),
    ("forest_settings.svg",  "Forest Settings",      "open_forest_settings" ),
    ("project_settings.svg", "Project Settings",     "open_project_settings"),
    ("add_data.svg",         "Ajouter des couches",  "open_add_data"        ),
]

QFIELD_BUTTONS = [
#   ("icon-file",        "tooltip",    "create_handler",           "merge_handler"          ),
    ("diagnostic.svg",   "Diagnostic", "open_diagnostic_create", "open_diagnostic_merge", "open_diagnostic_load"),
    ("pedology.svg",     "Pédologie",  "open_pedology_create",     "open_pedology_import", None),
    ("tree_marking.svg", "Martelage",  "open_tree_marking_create", "open_tree_marking_merge", "open_tree_marking_load"),
    ("expertise.svg",    "Expertise",  "open_expertise_create",    "open_expertise_merge", "open_expertise_load"),
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

class Qsequoia2Racines:
    def __init__(self, iface):
        self.iface = iface

        self.plugin_dir = Path(__file__).parent
        self.plugin_name = "Qsequoia2 – Racines"

        self.toolbar = None
        self.buttons = []

        # Classic dialogs
        self.global_dialog = None
        self.forest_dialog = None
        self.project_dialog = None
        self.add_data_dialog = None

        # QField dialogs
        self.diagnostic_create = None
        self.diagnostic_merge = None
        self.diagnostic_load = None
        self.pedology_create = None
        self.pedology_import = None
        self.tree_marking_create = None
        self.tree_marking_merge = None
        self.tree_marking_load = None
        self.expertise_create = None
        self.expertise_merge = None
        self.expertise_load = None

    def initGui(self):
        # initGui() is called by QGIS when the plugin is enabled in the UI
        # initGui() is specifically meant to register GUI elements (toolbars, menus, buttons, etc.).

        # Toolbar
        self.toolbar = self.iface.addToolBar(self.plugin_name)
        self.toolbar.setObjectName("Qsequoia2RacinesToolbar")

        for icon, tooltip, handler in CLASSIC_BUTTONS:
            btn = ClassicButton(
                icon = self.plugin_dir / "icons" / icon,
                tooltip = tooltip,
                slot = getattr(self, handler),
                iface = self.iface,
                plugin_name = self.plugin_name
            )
            self.buttons.append(btn)

        for icon, tooltip, create_handler, merge_handler, load_handler in QFIELD_BUTTONS:

            menu_items = []

            if create_handler and hasattr(self, create_handler):
                menu_items.append(("Créer", getattr(self, create_handler)))

            if merge_handler and hasattr(self, merge_handler):
                menu_items.append(("Combiner", getattr(self, merge_handler)))

            if load_handler and hasattr(self, load_handler):
                menu_items.append(("Charger", getattr(self, load_handler)))

            btn = QfieldButton(
                icon=self.plugin_dir / "icons" / icon,
                tooltip=tooltip,
                menu_items=menu_items
            )

            self.buttons.append(btn)

        for btn in self.buttons:
            btn.add_to_toolbar(self.toolbar)
            
    # region HANDLERS
    def open_global_settings(self):
        if not self.global_dialog:
            self.global_dialog = GlobalSettingsDialog()
        self.global_dialog.exec_()
        
    def open_forest_settings(self):
        if not self.forest_dialog:
            self.forest_dialog = ForestSettingsDialog(self.iface)
        self.forest_dialog.exec_()

    def open_project_settings(self):
        forest = get_project_variable("forest_prefix")
        if not forest:
            QMessageBox.warning(self.iface.mainWindow(), "Forêt non sélectionnée","Veuillez sélectionner une forêt avant de lancer un projet de carte.")
            return
          
        if not self.project_dialog:
            self.project_dialog = ProjectSettingsDialog(self.iface)
        self.project_dialog.exec_()
    
    def open_add_data(self):
        if not self._check_style_dir_is_selected():
            return None
        if not self._check_forest_is_selected():
            return None
        
        if not self.add_data_dialog:
            self.add_data_dialog = AddDataDialog(self.iface)
        self.add_data_dialog.exec_()

    # endregion

    # region DIAGNOSTIC
    def open_diagnostic_create(self):
        if not self._check_seq_dir():
            return None
        
        if not self.diagnostic_create:
            self.diagnostic_create = DiagnosticCreateDialog()
        self.diagnostic_create.exec_()

    def open_diagnostic_merge(self):
        if not self._check_seq_dir():
            return None

        if not self.diagnostic_merge:
            self.diagnostic_merge = DiagnosticMergeDialog()
        self.diagnostic_merge.exec_()

    def open_diagnostic_load(self):
        if not self._check_seq_dir():
            return None

        if not self.diagnostic_load:
            self.diagnostic_load = DiagnosticLoad()
        self.diagnostic_load.load()
        
    # endregion
        
    # region PEDOLOGY
    def open_pedology_create(self):
        if not self._check_forest_is_selected():
            return None
        
        if not self.pedology_create:
            self.pedology_create = PedologyCreateDialog(self.iface)
        self.pedology_create.exec_()

    def open_pedology_import(self):
        return
    
    # endregion
    
    # region TREE MARKING
    def open_tree_marking_create(self):
        if not self.tree_marking_create:
            self.tree_marking_create = TreeMarkingCreateDialog()
        self.tree_marking_create.exec_()

    def open_tree_marking_merge(self):
        if not self.tree_marking_merge:
            self.tree_marking_merge = TreeMarkingMergeDialog()
        self.tree_marking_merge.exec_()

    def open_tree_marking_load(self):
        if not self.tree_marking_load:
            self.tree_marking_load = TreeMarkingLoad()
        self.tree_marking_load.load()
    # endregion

    # region EXPERTISE
    def open_expertise_create(self):
        if not self._check_seq_dir():
            return None
        
        if not self.expertise_create:
            self.expertise_create = ExpertiseCreateDialog()
        self.expertise_create.exec_()
        
    def open_expertise_merge(self):
        if not self._check_seq_dir():
            return None

        if not self.expertise_merge:
            self.expertise_merge = ExpertiseMergeDialog()
        self.expertise_merge.exec_()

    def open_expertise_load(self):
        if not self._check_seq_dir():
            return None
        
        if not self.expertise_load:
            self.expertise_load = ExpertiseLoad()
        self.expertise_load.load()
        
    # endregion
    
    def _check_seq_dir(self):
        seq_dir = get_project_variable("QS2_seq_dir")
        if not seq_dir:
            QMessageBox.warning(self.iface.mainWindow(), "Forêt non sélectionnée", "Veuillez sélectionner une forêt.")
            return False
        return True
    
    def _check_forest_is_selected(self):
        forest = get_project_variable("forest_prefix")
        if not forest:
            QMessageBox.warning(self.iface.mainWindow(), "Forêt non sélectionnée","Veuillez sélectionner une forêt.")
            return False
        return True

    def _check_style_dir_is_selected(self):
        style_dir = get_global_variable("styles_directory")

        # 1. Global variable not set
        if not style_dir:
            QMessageBox.warning(
                self.iface.mainWindow(), 
                "Bibliothèque de styles non sélectionnée",
                "Veuillez sélectionner un dossier 'Bibliothèque de styles' dans les paramètres globaux."
            )
            return False

        # Convert to Path
        style_path = Path(style_dir)

        # 2. Directory does not exist
        if not style_path.exists() or not style_path.is_dir():
            QMessageBox.warning(
                self.iface.mainWindow(),
                "Dossier introuvable",
                f"Le dossier indiqué n’existe pas :\n{style_dir}"
            )
            return False

        # 3. Check that at least one .qml file exists
        if not any(style_path.glob("*.qml")):
            QMessageBox.warning(
                self.iface.mainWindow(),
                "Aucun style trouvé",
                f"Le dossier sélectionné ne contient aucun fichier .qml :\n{style_dir}"
            )
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
