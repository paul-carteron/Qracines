from PyQt5.QtWidgets import QDialog, QFileDialog
from PyQt5.QtCore import QVariant
from PyQt5.QtGui import QFont
from qgis.core import QgsFieldConstraints, QgsFeatureRequest, QgsExpression, QgsPalLayerSettings, QgsTextFormat, QgsVectorLayerSimpleLabeling

from .tree_marking_dialog import Ui_Tree_markingDialog
from Qsequoia2.utils.database_utils import DatabaseManager
from Qsequoia2.layer import LayerManager

class Tree_markingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Tree_markingDialog()
        self.ui.setupUi(self)


gpkg_path = "C:\\Users\\PaulCarteron\\Desktop\\New Qfield\\inventaire.gpkg"
arbres_fields = [
    ("ID_CODE", QVariant.String),
    ("UUID", QVariant.String), ("PARCELLE", QVariant.String), ("ESSENCE_ID", QVariant.String),
    ("ESSENCE_SECONDAIRE_ID", QVariant.String), ("DIAMETRE", QVariant.LongLong), ("EFFECTIF", QVariant.LongLong),
    ("HAUTEUR", QVariant.LongLong), ("FAVORI", QVariant.Bool), ("OBSERVATION", QVariant.String),
    ("COMPTEUR", QVariant.LongLong),
]
arbres = create_memory_layer('arbres', arbres_fields, 'Point')

# Load essences from DB
essences = DatabaseManager().load_essences()
[write_layer_to_gpkg(layer, gpkg_path) for layer in (arbres, essences)]
add_layers_from_gpkg(gpkg_path)

# Load layers into LayerManager
arbres = LayerManager('arbres')
essences = LayerManager('essences')

# ESSENCE value map
query_string = " OR ".join([f"code = '{code}'" for code in codes])
request = QgsFeatureRequest(QgsExpression(query_string))
essences_list = [{f"{ess['code']}{' ' + ess['variation'] if ess['variation'] else ''}": ess['fid']} for ess in essences.layer.getFeatures(request)]
config = {'map': essences_list }
arbres.fields.add_value_map('ESSENCE_ID', config)

# ESSENCE SECONDAIRE
essences.fields.add_field("selected", QVariant.Bool)
filter_str = f"code NOT IN ({', '.join(map(lambda e: f'\'{e}\'', codes))})"
request = QgsFeatureRequest().setFilterExpression(filter_str)
essences.layer.startEditing()
for feature in essences.layer.getFeatures(request):
    feature["selected"] = True
    essences.layer.updateFeature(feature)
essences.layer.commitChanges()

# RELATION
config = {
    'FilterExpression': '"selected" = True',
    'Key': 'fid',
    'Layer': essences.layer.id(),
    'Value': 'essence_variation',
    'AllowNull': True
}
arbres.fields.add_value_relation('ESSENCE_SECONDAIRE_ID', config)

# FORM SETUP
required_fields = ["UUID", "PARCELLE", "DIAMETRE", "EFFECTIF"]
for field in required_fields:
    arbres.fields.set_constraint(field, QgsFieldConstraints.ConstraintNotNull)

aliases = [("ID_CODE", "CODE"), ("ESSENCE_ID", "ESSENCE"), ("ESSENCE_SECONDAIRE_ID", "ESSENCE SECONDAIRE"), ("FAVORI", "⭐"), ("COMPTEUR", "ID")]
for field, alias in aliases:
    arbres.fields.set_alias(field, alias)

for field in ["COMPTEUR", "ID_CODE"]:
    arbres.fields.set_read_only(field)

arbres.fields.set_default_value("fid", 'if (maximum("fid") is NULL, 1 ,maximum("fid") + 1)')

arbres.fields.set_default_value("ID_CODE", """
WITH_VARIABLE(
    'ess',
    get_feature(
        'essences',
        '_uid_',
        coalesce(NULLIF("ESSENCE_ID", ''), "ESSENCE_SECONDAIRE_ID")
    ),
    concat(
        "COMPTEUR",
        ': ',
        attribute(@ess, 'code'),
        CASE
            WHEN attribute(@ess, 'variation') IS NOT NULL
            THEN concat(' ', attribute(@ess, 'variation'))
            ELSE ''
        END,
        ' D', "DIAMETRE",
        CASE
            WHEN "HAUTEUR" IS NOT NULL AND "HAUTEUR" != ''
            THEN concat(' H', "HAUTEUR")
            ELSE ''
        END
    )
)
""")

arbres.fields.set_constraint("UUID", QgsFieldConstraints.ConstraintUnique)
arbres.fields.set_default_value("UUID", "uuid()")
arbres.fields.set_reuse_last_value("PARCELLE")

# Constraint expressions
ess_expr = """
((COALESCE("ESSENCE_ID", '') <> '') AND "ESSENCE_SECONDAIRE_ID" IS NULL)
OR
((COALESCE("ESSENCE_ID", '') = '') AND "ESSENCE_SECONDAIRE_ID" IS NOT NULL)
"""
msg = "Veuillez sélectionner une valeur pour ESSENCE ou ESSENCE_SECONDAIRE (mais pas les deux)."
arbres.fields.set_constraint_expression('ESSENCE_ID', ess_expr, msg, QgsFieldConstraints.ConstraintStrengthHard)
arbres.fields.set_constraint_expression('ESSENCE_SECONDAIRE_ID', ess_expr, msg, QgsFieldConstraints.ConstraintStrengthHard)

# Value maps and widgets
arbres.fields.add_value_map('DIAMETRE', {str(d): str(d) for d in range(15, 151, 5)})
arbres.fields.add_value_map('HAUTEUR', {str(h): str(h) for h in range(2, 20)})
arbres.fields.add_value_map('OBSERVATION', {v: v for v in ["Chablis", "Bio", "Ehouppé", "Cablage"]})
arbres.fields.add_value_map('FAVORI', {"FALSE": "FALSE"})
arbres.fields.add_value_relation('EFFECTIF', {'AllowNull': False, 'Max': 1000, 'Min': 0, 'Precision': 0, 'Step': 1})
arbres.fields.set_default_value("EFFECTIF", '1', False)
arbres.fields.set_default_value("COMPTEUR", 'count("fid") + 1')

# Labeling
label_settings = QgsPalLayerSettings()
label_settings.fieldName = "COMPTEUR"
text_format = QgsTextFormat()
text_format.setFont(QFont("Arial", 12))
text_format.setSize(12)
label_settings.setFormat(text_format)
labeling = QgsVectorLayerSimpleLabeling(label_settings)
arbres.layer.setLabeling(labeling)
arbres.layer.setLabelsEnabled(True)
arbres.layer.triggerRepaint()

# Create form layout
form_fields = ["COMPTEUR", "PARCELLE", "ESSENCE_ID", "ESSENCE_SECONDAIRE_ID", "DIAMETRE", "HAUTEUR", "EFFECTIF", "OBSERVATION", "FAVORI", "ID_CODE"]
arbres.forms.init_drag_and_drop_form()
arbres.forms.add_fields_to_tab(form_fields, tab_name="Info")

# QField-specific sync setting
arbres.layer.setCustomProperty("QFieldSync/value_map_button_interface_threshold", 99)