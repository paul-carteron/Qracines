from qgis.PyQt.QtWidgets import QMessageBox, QToolButton, QMenu
from qgis.PyQt.QtGui import QIcon

from .modules.diagnostic.create.diagnostic_create import DiagnosticCreateDialog
from .modules.diagnostic.merge.diagnostic_merge import DiagnosticMergeDialog
from .modules.diagnostic.load.diagnostic_load import DiagnosticLoad

from .modules.expertise.create.expertise_create import ExpertiseCreateDialog
from .modules.expertise.merge.expertise_merge import ExpertiseMergeDialog
from .modules.expertise.load.expertise_load import ExpertiseLoad

from .modules.pedology.pedology_create import PedologyCreateDialog

from .modules.tree_marking.create.tree_marking_create import TreeMarkingCreateDialog
from .modules.tree_marking.merge.tree_marking_merge import TreeMarkingMergeDialog
from .modules.tree_marking.load.tree_marking_load import TreeMarkingLoad

# import utils
from .utils.variable import get_project_variable

from pathlib import Path

QFIELD_BUTTONS = [
#   ("icon-file",        "tooltip",    "create_handler",           "merge_handler"          ),
    ("diagnostic.svg",   "Diagnostic", "open_diagnostic_create", "open_diagnostic_merge", "open_diagnostic_load"),
    ("pedology.svg",     "Pédologie",  "open_pedology_create",     "open_pedology_import", None),
    ("tree_marking.svg", "Martelage",  "open_tree_marking_create", "open_tree_marking_merge", "open_tree_marking_load"),
    ("expertise.svg",    "Expertise",  "open_expertise_create",    "open_expertise_merge", "open_expertise_load"),
]

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

    # region DIAGNOSTIC
    def open_diagnostic_create(self):
        if not self._check_seq_dir():
            return None
        
        self._check_seq_style_dir()
        
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
        
    # # region PEDOLOGY
    # def open_pedology_create(self):
    #     if not self._check_forest_is_selected():
    #         return None
        
    #     if not self.pedology_create:
    #         self.pedology_create = PedologyCreateDialog(self.iface)
    #     self.pedology_create.exec_()

    # def open_pedology_import(self):
    #     return
    
    # # endregion
    
    # region TREE MARKING
    def open_tree_marking_create(self):
        self._check_seq_style_dir()
        
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
        
        self._check_seq_style_dir()

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
            QMessageBox.warning(
                self.iface.mainWindow(),
                "Forêt non sélectionnée",
                "Veuillez sélectionner une forêt avec le plugin Qsequoia2"
                )
            return False
        return True
    
    def _check_seq_style_dir(self):
        style_dir = get_project_variable("QS2_styles_directory")
        if not style_dir:
            QMessageBox.warning(
                self.iface.mainWindow(),
                "Styles non sélectionnés.",
                "Pas de dossier de styles sélectionné avec le plugin Qsequoia2. Les couches ne seront pas stylisées."
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
