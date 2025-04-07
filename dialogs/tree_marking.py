from PyQt5.QtWidgets import QDialog, QFileDialog
from PyQt5.QtCore import QVariant
from PyQt5.QtGui import QFont
from qgis.core import QgsFieldConstraints, QgsFeatureRequest, QgsExpression, QgsPalLayerSettings, QgsTextFormat, QgsVectorLayerSimpleLabeling

from .tree_marking_dialog import Ui_Tree_markingDialog
from ..utils.structure_utils import get_path
from ..utils.qfield_utils import create_memory_layer, write_layer_to_gpkg, add_layers_from_gpkg
from ..utils.database_utils import DatabaseManager
from ..layer_manager import LayerManager

def create_tree_marking(codes = ['CHE', 'HET']):
    # param
    essences = DatabaseManager().load_essences()
    essences_list = list(dict.fromkeys([ess["essence"] for ess in essences.getFeatures()]))

    # create arbres layer
    arbres_fields = [
        ("ID_CODE", QVariant.String),
        ("UUID", QVariant.String), ("PARCELLE", QVariant.String), ("ESSENCE_ID", QVariant.String),
        ("ESSENCE_SECONDAIRE_ID", QVariant.String), ("DIAMETRE", QVariant.LongLong), ("EFFECTIF", QVariant.LongLong),
        ("HAUTEUR", QVariant.LongLong), ("FAVORI", QVariant.Bool), ("OBSERVATION", QVariant.String),
        ("COMPTEUR", QVariant.LongLong),
    ]
    arbres = create_memory_layer(layer_name = 'arbres', fields_list = arbres_fields,  geometry = 'Point')

    # write layer to geopackage and load them into QGIS
    gpkg_path = get_path("inventaire")
    [write_layer_to_gpkg(layer, gpkg_path) for layer in (arbres, essences)]
    add_layers_from_gpkg(gpkg_path)

    # Load layers using LayerManager
    arbres = LayerManager("arbres")
    essences = LayerManager("essences")

    # --- ESSENCE value map (for main ESSENCE_ID field)
    query_expr = " OR ".join([f"code = '{code}'" for code in codes])
    request = QgsFeatureRequest(QgsExpression(query_expr))

    essences_for_button = []
    for feature in essences.layer.getFeatures(request):
        label = f"{feature['code']}{' ' + feature['variation'] if feature['variation'] else ''}"
        essences_for_button.append({label: feature['fid']})

    arbres.fields.add_value_map("ESSENCE_ID", {"map": essences_for_button})

    # --- ESSENCE SECONDAIRE logic
    # Add 'selected' field if not present
    if "selected" not in [f.name() for f in essences.layer.fields()]:
        essences.fields.add_field("selected", QVariant.Bool)

    # Set 'selected = True' for secondary essences
    excluded_codes = ", ".join([f"'{code}'" for code in codes])
    expression = f"code NOT IN ({excluded_codes})"
    essences.fields.set_field_value_by_expression("selected", True, expression)

    # RELATION
    config = {
        'FilterExpression': '"selected" = True',
        'Key': 'fid',
        'Layer': essences.layer.id(),
        'Value': 'essence_variation',
        'AllowNull': True
    }
    arbres.fields.add_value_relation('ESSENCE_SECONDAIRE_ID', config)

    # FIELDS SETUP
    required_fields = ["UUID", "PARCELLE", "DIAMETRE", "EFFECTIF"]
    for field in required_fields:
        arbres.fields.set_constraint(field, QgsFieldConstraints.ConstraintNotNull)

    aliases = [("ID_CODE", "CODE"), ("ESSENCE_ID", "ESSENCE"), ("ESSENCE_SECONDAIRE_ID", "ESSENCE SECONDAIRE"), ("FAVORI", "⭐"), ("COMPTEUR", "ID")]
    for field, alias in aliases:
        arbres.fields.set_alias(field, alias)

    for field in ["COMPTEUR", "ID_CODE"]:
        arbres.fields.set_read_only(field)

    ## FID
    arbres.fields.set_default_value("fid", 'if (maximum("fid") is NULL, 1 ,maximum("fid") + 1)')

    ## UUID
    arbres.fields.set_constraint("UUID", QgsFieldConstraints.ConstraintUnique)
    arbres.fields.set_default_value("UUID", "uuid()")

    ## COMPTEUR
    arbres.fields.set_default_value("COMPTEUR", 'count("fid") + 1')

    ## PARCELLE
    arbres.fields.set_reuse_last_value("PARCELLE")

    ## ESSENCE_ID & ESSENCE_SECONDAIRE_ID
    ess_expr = """
    ((COALESCE("ESSENCE_ID", '') <> '') AND "ESSENCE_SECONDAIRE_ID" IS NULL)
    OR
    ((COALESCE("ESSENCE_ID", '') = '') AND "ESSENCE_SECONDAIRE_ID" IS NOT NULL)
    """
    msg = "Veuillez sélectionner une valeur pour ESSENCE ou ESSENCE_SECONDAIRE (mais pas les deux)."
    arbres.fields.set_constraint_expression('ESSENCE_ID', ess_expr, msg, QgsFieldConstraints.ConstraintStrengthHard)
    arbres.fields.set_constraint_expression('ESSENCE_SECONDAIRE_ID', ess_expr, msg, QgsFieldConstraints.ConstraintStrengthHard)

    ## DIAMETRE
    arbres.fields.add_value_map('DIAMETRE', {str(d): str(d) for d in range(15, 151, 5)})

    ## HAUTEUR
    arbres.fields.add_value_map('HAUTEUR', {str(h): str(h) for h in range(2, 20)})

    ## EFFECTIF
    arbres.fields.add_value_relation('EFFECTIF', {'AllowNull': False, 'Max': 1000, 'Min': 0, 'Precision': 0, 'Step': 1})
    arbres.fields.set_default_value("EFFECTIF", '1', False)

    ## OBSERVATION
    arbres.fields.add_value_map('OBSERVATION', {v: v for v in ["Chablis", "Bio", "Ehouppé", "Cablage"]})

    ## FAVORI
    arbres.fields.add_value_map('FAVORI', {"FALSE": "FALSE"})

    ## ID_CODE
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