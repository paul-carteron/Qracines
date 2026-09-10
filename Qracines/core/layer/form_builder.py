from qgis.core import (
    Qgis,
    QgsAttributeEditorField,
    QgsAttributeEditorContainer,
    QgsAttributeEditorRelation,
    QgsOptionalExpression,
    QgsExpression
)

class FormBuilder:
    def __init__(self, layer):
        self.layer = layer
        self.config = self.layer.editFormConfig()
        self.root = None  # delay initialization until layout is set

    def init_form(self):
        self.config.setLayout(Qgis.AttributeFormLayout.DragAndDrop)
        self.config.clearTabs()
        self.layer.setEditFormConfig(self.config)
        self.root = self.config.invisibleRootContainer() 

    def get_tab(self, name: str):
        """Return an existing tab container by name, or None."""
        for child in self.root.children():
            if (
                isinstance(child, QgsAttributeEditorContainer)
                and child.type() == Qgis.AttributeEditorContainerType.Tab
                and child.name() == name
            ):
                return child
        return None

    def create_tab(self, name: str, clear=True):
        """Create or get a tab container."""
        tab = self.get_tab(name)
        if tab and clear:
            tab.clear()
            return tab
        if tab:
            return tab
        tab = QgsAttributeEditorContainer(name, self.root)
        tab.setType(Qgis.AttributeEditorContainerType.Tab)
        self.root.addChildElement(tab)
        return tab

    def add_group(
        self,
        name: str = "Group",
        parent=None,
        columns=1,
        visibility_expression=None,
    ):
        """Create a group box inside a container (or at root if no parent)."""
        parent = parent or self.root  # default fallback

        group = QgsAttributeEditorContainer(name, parent)
        group.setType(Qgis.AttributeEditorContainerType.GroupBox)
        group.setColumnCount(columns)
        if visibility_expression:
            group.setVisibilityExpression(
                QgsOptionalExpression(QgsExpression(visibility_expression))
            )
        parent.addChildElement(group)
        return group

    def add_fields(self, field_names, parent=None):
        parent = parent or self.root  # default fallback
        for fname in field_names:
            idx = self.layer.fields().indexFromName(fname)
            if idx == -1:
                print(f"⚠️ Field '{fname}' not found in layer '{self.layer.name()}'")
                continue
            field = QgsAttributeEditorField(fname, idx, parent)
            parent.addChildElement(field)

    def add_relation(
        self,
        relation,
        parent=None,
        alias=None,
        visibility_expression=None,
    ):
        """Add a relation widget to a container (usually a tab)."""
        if relation is None or not relation.isValid():
            return

        parent = parent or self.root
        if visibility_expression:
            parent.setVisibilityExpression(
                QgsOptionalExpression(QgsExpression(visibility_expression))
            )

        relation_editor = QgsAttributeEditorRelation(relation, parent)
        if alias:
            relation_editor.setLabel(alias)
            relation_editor.setShowLabel(True)
        parent.addChildElement(relation_editor)

        return relation_editor

    def apply(self):
        """Apply changes to the layer form."""
        self.layer.setEditFormConfig(self.config)
