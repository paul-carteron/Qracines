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

    def add_fields(self, *field_names, name=None, clear_tab=False, columns=1, visibility_expression=None, type="group"):
        container = self._get_or_create_container(name, clear_tab, type=type)
        container.setColumnCount(int(columns))
        if visibility_expression:
            container.setVisibilityExpression(QgsOptionalExpression(QgsExpression(visibility_expression)))

        for name in field_names:
            index = self.layer.fields().indexFromName(name)
            if index != -1:
                field = QgsAttributeEditorField(name, index, container)
                container.addChildElement(field)

        self.layer.setEditFormConfig(self.config)

    def _get_or_create_container(self, name, clear_tab=False, type="group"):
        if not name:
            return self.root

        existing = next(
            (
                child
                for child in self.root.children()
                if isinstance(child, QgsAttributeEditorContainer)
                and child.name() == name
            ),
            None,
        )

        if existing and clear_tab:
            existing.clear()
            return existing

        if existing:
            return existing
            
        new_container = QgsAttributeEditorContainer(name, self.root)
        
        if type.lower() == "tab":
            new_container.setType(Qgis.AttributeEditorContainerType.Tab)
        elif type.lower() == "group":
            new_container.setType(Qgis.AttributeEditorContainerType.GroupBox)
        elif type.lower() == "row":
            new_container.setType(Qgis.AttributeEditorContainerType.Row)
        else:
            raise ValueError(f"Unknown container type: {type}")

        print(new_container.type())
        self.root.addChildElement(new_container)
        return new_container

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

    def create_group(self, name: str = "Group", parent=None, columns=1):
        """Create a group box inside a container (or at root if no parent)."""
        parent = parent or self.root  # default fallback

        group = QgsAttributeEditorContainer(name, parent)
        group.setType(Qgis.AttributeEditorContainerType.GroupBox)
        group.setColumnCount(columns)
        parent.addChildElement(group)
        return group

    def new_add_fields(self, field_names, parent = None):
        parent = parent or self.root  # default fallback
        for fname in field_names:
            idx = self.layer.fields().indexFromName(fname)
            if idx == -1:
                print(f"⚠️ Field '{fname}' not found in layer '{self.layer.name()}'")
                continue
            field = QgsAttributeEditorField(fname, idx, parent)
            parent.addChildElement(field)

    def new_add_relation(self, relation, parent, visibility_expression=None):
        """Add a relation widget to a container (usually a tab)."""
        if relation is None or not relation.isValid():
            return

        if visibility_expression:
            parent.setVisibilityExpression(
                QgsOptionalExpression(QgsExpression(visibility_expression))
            )

        relation_editor = QgsAttributeEditorRelation(relation, parent)
        parent.addChildElement(relation_editor)

        return relation_editor

    def apply(self):
        """Apply changes to the layer form."""
        self.layer.setEditFormConfig(self.config)