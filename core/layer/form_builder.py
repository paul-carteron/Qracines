from qgis.core import (
    Qgis,
    QgsAttributeEditorField,
    QgsAttributeEditorContainer,
    QgsAttributeEditorRelation,
    QgsOptionalExpression,
    QgsExpression
)
from .fetcher import LayerFetcher


class FormBuilder:
    def __init__(self, layer):
        self.layer = layer
        self.config = self.layer.editFormConfig()
        self.root = None  # delay initialization until layout is set

    def init_drag_and_drop_form(self):
        self.config.setLayout(Qgis.AttributeFormLayout.DragAndDrop)
        self.config.clearTabs()
        self.layer.setEditFormConfig(self.config)
        self.root = self.config.invisibleRootContainer() 

    def add_fields(self, *field_names, name=None, clear_tab=False, columns=1, visibility_expression=None, type="group"):
        tab = self._get_or_create_container(name, clear_tab, type=type)
        tab.setColumnCount(int(columns))
        if visibility_expression:
            tab.setVisibilityExpression(QgsOptionalExpression(QgsExpression(visibility_expression)))

        for name in field_names:
            index = self.layer.fields().indexFromName(name)
            if index != -1:
                field = QgsAttributeEditorField(name, index, tab)
                tab.addChildElement(field)

        self.layer.setEditFormConfig(self.config)

    def add_relation(self, relation_name, name=None, visibility_expression=None, type="group"):
        relation = LayerFetcher.get_relation_by_name(relation_name)
        if not relation:
            print(f"Relation '{relation_name}' not found.")
            return

        tab = self._get_or_create_container(name, type=type)
        if visibility_expression:
            tab.setVisibilityExpression(QgsOptionalExpression(QgsExpression(visibility_expression)))
        
        relation_editor = QgsAttributeEditorRelation(relation, tab)
        tab.addChildElement(relation_editor)
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

        if existing:
            return existing
        
        if clear_tab:
            existing.clear()
            
        print(type)
        new_container = QgsAttributeEditorContainer(name, self.root)
        
        print(new_container)
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
