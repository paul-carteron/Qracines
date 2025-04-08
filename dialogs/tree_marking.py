from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtCore import QVariant
from PyQt5.QtGui import QFont
from qgis.core import (
  QgsProject,
  QgsRasterLayer,
  QgsFieldConstraints,
  QgsFeatureRequest,
  QgsExpression,
  QgsPalLayerSettings,
  QgsTextFormat,
  QgsVectorLayerSimpleLabeling
  )

import os

from .tree_marking_dialog import Ui_Tree_markingDialog

from ..core.db.manager import DatabaseManager
from ..core.layer.manager import LayerManager

from ..utils.path_manager import get_path, get_style, find_similar_filenames
from ..utils.qfield_utils import create_memory_layer, write_layer_to_gpkg, add_layers_from_gpkg
from ..utils.variable_utils import create_new_projet_with_variables

class Tree_markingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Tree_markingDialog()
        self.ui.setupUi(self)

        self.raster_checkboxes = {
            "plt": self.ui.checkBox_PLT,
            "plt_anc": self.ui.checkBox_PLTANC,
            "irc": self.ui.checkBox_IRC,
            "rgb": self.ui.checkBox_RGB,
            "mnh": self.ui.checkBox_MNH,
            "scan25": self.ui.checkBox_SCAN,
        }

        self.ui.buttonBox.accepted.connect(self.run_and_close)
        self.ui.buttonBox.rejected.connect(self.reject)

        self.ui.pushButton_add.clicked.connect(self.add_selected_species)
        self.ui.pushButton_remove.clicked.connect(self.remove_selected_species)

        self.populate_species_list()

    def populate_species_list(self):
        self.essences = DatabaseManager().load_essences()
        self.essence_lookup = {}

        unique_essences = []

        for feat in self.essences.getFeatures():
            name = feat["essence"]
            code = feat["code"]
            if name not in self.essence_lookup:
                self.essence_lookup[name] = code
                unique_essences.append(name)

        self.ui.listWidget_spiecies.addItems(unique_essences)

    def add_selected_species(self):
        selected_items = self.ui.listWidget_spiecies.selectedItems()
        for item in selected_items:
            text = item.text()
            if not self.is_in_list(self.ui.listWidget_spiecies_selected, text):
                self.ui.listWidget_spiecies_selected.addItem(text)

    def remove_selected_species(self):
        for item in self.ui.listWidget_spiecies_selected.selectedItems():
            row = self.ui.listWidget_spiecies_selected.row(item)
            self.ui.listWidget_spiecies_selected.takeItem(row)

    @staticmethod
    def is_in_list(list_widget, text):
        return any(list_widget.item(i).text() == text for i in range(list_widget.count()))

    def run_and_close(self):
        
        create_new_projet_with_variables()

        selected_essences = [self.ui.listWidget_spiecies_selected.item(i).text() for i in range(self.ui.listWidget_spiecies_selected.count())]
        selected_codes = [self.essence_lookup[ess] for ess in selected_essences if ess in self.essence_lookup]

        if not selected_codes:
            QMessageBox.warning(self, "No species selected", "Please select at least one species.")
            return

        # Optional: collect other inputs (spinboxes, checkboxes, etc.)
        dmin = self.ui.spinBox_Dmin.value()
        dmax = self.ui.spinBox_Dmax.value()
        hmin = self.ui.spinBox_Hmin.value()
        hmax = self.ui.spinBox_Hmax.value()

        # Call your core function
        self.create_tree_marking(
            selected_codes,
            dmin,
            dmax,
            hmin,
            hmax
        )

        self.load_selected_rasters()
        self.accept()  # Close dialog on success

    def create_tree_marking(self, codes, dmin, dmax, hmin, hmax):

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
        [write_layer_to_gpkg(layer, gpkg_path) for layer in (arbres, self.essences)]
        add_layers_from_gpkg(gpkg_path)

        # Load layers using LayerManager
        arbres = LayerManager("arbres")
        essences = LayerManager("essences")

        # --- ESSENCE value map (for main ESSENCE_ID field)
        query_string = " OR ".join([f"code = '{code}'" for code in codes])
        request = QgsFeatureRequest(QgsExpression(query_string))

        essences_list = [{f"{ess['code']}{' ' + ess['variation'] if ess['variation'] else ''}": ess['fid']} for ess in essences.layer.getFeatures(request)]
        arbres.fields.add_value_map('ESSENCE_ID', {'map': essences_list })

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
        arbres.fields.add_value_map('DIAMETRE', {'map': [{str(d): str(d)} for d in range(dmin, dmax, 5)]})

        ## HAUTEUR
        arbres.fields.add_value_map('HAUTEUR', {'map': [{str(h): str(h)} for h in range(hmin, hmax)]})

        ## EFFECTIF
        arbres.fields.add_range('EFFECTIF', {'AllowNull': False, 'Max': 1000, 'Min': 0, 'Precision': 0, 'Step': 1})
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
        arbres.forms.add_fields_to_tab(form_fields)

        # QField-specific sync setting
        arbres.layer.setCustomProperty("QFieldSync/value_map_button_interface_threshold", 99)

    def load_selected_rasters(self):
        for logical_key, checkbox in self.raster_checkboxes.items():
            if checkbox.isChecked():
                try:
                    # Load raster
                    raster_path = get_path(logical_key)
                    if not os.path.exists(raster_path):
                        message = f"Le fichier raster pour {logical_key} est introuvable :\n{raster_path}"

                        # Recherche de fichiers similaires 
                        similar_files = find_similar_filenames(raster_path, logical_key)
                        if similar_files:
                            suggestions = "\n".join(similar_files)
                            message += (
                                f"\n\nFichiers similaires trouvés dans le dossier :\n{suggestions}"
                                "\n\nVeuillez renommer le fichier manquant si l’un d’eux correspond."
                            )

                    QMessageBox.information(self, "Raster manquant", message)
                    continue

                    layer = QgsRasterLayer(raster_path, logical_key)
                    if not layer.isValid():
                        raise Exception(f"Raster invalide : {raster_path}")

                    # Try to load style if defined
                    try:
                        style_path = get_style(logical_key)
                        layer.loadNamedStyle(style_path)
                        layer.triggerRepaint()
                    except (KeyError, ValueError, FileNotFoundError):
                        pass  # Style is optional and explicitly declared, so silently skip if not found

                    QgsProject.instance().addMapLayer(layer)

                except Exception as e:
                    QMessageBox.warning(self, "Erreur de chargement", f"Impossible de charger {logical_key} : {str(e)}")