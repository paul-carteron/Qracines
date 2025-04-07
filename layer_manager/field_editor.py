from qgis.core import (
    QgsField,
    QgsFieldConstraints,
    QgsDefaultValue,
    QgsEditorWidgetSetup
)


class FieldEditor:
    def __init__(self, layer):
        self.layer = layer

    def _get_field_index(self, field_name):
        index = self.layer.fields().indexFromName(field_name)
        if index == -1:
            raise ValueError(f"Field '{field_name}' not found in layer '{self.layer.name()}'.")
        return index

    def add_field(self, name, field_type):
        self.layer.startEditing()
        self.layer.dataProvider().addAttributes([QgsField(name, field_type)])
        self.layer.updateFields()
        self.layer.commitChanges()

    def set_default_value(self, field_name, default_value, apply_on_update=True):
        index = self._get_field_index(field_name)
        self.layer.setDefaultValueDefinition(index, QgsDefaultValue(default_value, apply_on_update))

    def set_constraint(self, field_name, constraint, strength=QgsFieldConstraints.ConstraintStrengthHard):
        index = self._get_field_index(field_name)
        self.layer.setFieldConstraint(index, constraint, strength)

    def set_constraint_expression(self, field_name, expression, description, strength=QgsFieldConstraints.ConstraintStrengthSoft):
        index = self._get_field_index(field_name)
        self.layer.setConstraintExpression(index, expression, description)
        self.layer.setFieldConstraint(index, QgsFieldConstraints.ConstraintExpression, strength)

    def set_alias(self, field_name, alias):
        index = self._get_field_index(field_name)
        self.layer.setFieldAlias(index, alias)

    def set_read_only(self, field_name):
        index = self._get_field_index(field_name)
        form_config = self.layer.editFormConfig()
        form_config.setReadOnly(index, True)
        self.layer.setEditFormConfig(form_config)

    def set_reuse_last_value(self, field_name):
        index = self._get_field_index(field_name)
        form_config = self.layer.editFormConfig()
        form_config.setReuseLastValue(index, True)
        self.layer.setEditFormConfig(form_config)

    def add_value_map(self, field_name, value_map):
        index = self._get_field_index(field_name)
        widget = QgsEditorWidgetSetup('ValueMap', {'map': value_map})
        self.layer.setEditorWidgetSetup(index, widget)

    def add_value_relation(self, field_name, config):
        index = self._get_field_index(field_name)
        widget = QgsEditorWidgetSetup('ValueRelation', config)
        self.layer.setEditorWidgetSetup(index, widget)