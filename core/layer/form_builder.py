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

    def add_fields_to_tab(self, *field_names, tab_name=None, clear_tab=False, columns=1, visibility_expression=None):
        tab = self._get_or_create_tab(tab_name, clear_tab)
        tab.setColumnCount(int(columns))
        if visibility_expression:
            tab.setVisibilityExpression(QgsOptionalExpression(QgsExpression(visibility_expression)))

        for name in field_names:
            index = self.layer.fields().indexFromName(name)
            if index != -1:
                field = QgsAttributeEditorField(name, index, tab)
                tab.addChildElement(field)

        self.layer.setEditFormConfig(self.config)

    def add_relation_to_tab(self, relation_name, tab_name=None, visibility_expression=None):
        relation = LayerFetcher.get_relation_by_name(relation_name)
        if not relation:
            print(f"Relation '{relation_name}' not found.")
            return

        tab = self._get_or_create_tab(tab_name)
        if visibility_expression:
            tab.setVisibilityExpression(QgsOptionalExpression(QgsExpression(visibility_expression)))
        relation_editor = QgsAttributeEditorRelation(relation, tab)
        tab.addChildElement(relation_editor)
        self.layer.setEditFormConfig(self.config)

    def _get_or_create_tab(self, tab_name, clear_tab=False):
        if not tab_name:
            return self.root

        existing = next((child for child in self.root.children()
                         if isinstance(child, QgsAttributeEditorContainer) and child.name() == tab_name), None)

        if existing and clear_tab:
            existing.clear()
            return existing

        if existing:
            return existing

        new_tab = QgsAttributeEditorContainer(tab_name, self.root)
        self.root.addChildElement(new_tab)
        return new_tab
