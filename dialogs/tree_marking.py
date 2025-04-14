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
  QgsVectorLayerSimpleLabeling,
  QgsOfflineEditing
  )

from qfieldsync.gui.package_dialog import PackageDialog

import os
import processing
import tempfile

from .tree_marking_dialog import Ui_Tree_markingDialog

from ..core.db.manager import DatabaseManager
from ..core.layer.manager import LayerManager

from ..utils.path_manager import get_path, get_style, find_similar_filenames
from ..utils.qfield_utils import create_memory_layer, zip_folder_contents, add_layers_from_gpkg
from ..utils.variable_utils import create_new_projet_with_variables

class Tree_markingDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
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

        self.essences_layer = DatabaseManager().load_essences()
        self.populate_species_list()

    def populate_species_list(self):
        self.essences_lookup = {}

        unique_essences = []

        for feat in self.essences_layer.getFeatures():
            name = feat["essence"]
            code = feat["code"]
            if name not in self.essences_lookup:
                self.essences_lookup[name] = code
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
        selected_codes = [self.essences_lookup[ess] for ess in selected_essences if ess in self.essences_lookup]

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
        self.package_for_qfield_and_zip()
        self.accept()  # Close dialog on success

    @staticmethod
    def create_arbres_layer():
        arbres_fields = [
            ("fid", QVariant.Int),
            ("ID_CODE", QVariant.String),
            ("UUID", QVariant.String),
            ("PARCELLE", QVariant.String),
            ("ESSENCE_ID", QVariant.String),
            ("ESSENCE_SECONDAIRE_ID", QVariant.String),
            ("DIAMETRE", QVariant.String),
            ("EFFECTIF", QVariant.LongLong),
            ("HAUTEUR", QVariant.String),
            ("FAVORI", QVariant.Bool),
            ("OBSERVATION", QVariant.String),
            ("COMPTEUR", QVariant.LongLong),
        ]

        arbres_layer = create_memory_layer(
            layer_name = 'arbres',
            fields_list = arbres_fields, 
            geometry = 'Point'
        )

        return arbres_layer
    
    @staticmethod
    def configure_form(arbres_manager):
        form_fields = ["COMPTEUR", "PARCELLE", "ESSENCE_ID", "ESSENCE_SECONDAIRE_ID", "DIAMETRE", "HAUTEUR", "EFFECTIF", "OBSERVATION", "FAVORI", "ID_CODE"]
        arbres_manager.forms.init_drag_and_drop_form()
        arbres_manager.forms.add_fields_to_tab(form_fields)

    @staticmethod
    def configure_essence_field(arbres_manager, essences_manager, codes):
        # 1. Build value map for main ESSENCE_ID field
        query_string = " OR ".join([f"code = '{code}'" for code in codes])
        request = QgsFeatureRequest(QgsExpression(query_string))

        essences_list = [
            {f"{ess['code']}{' ' + ess['variation'] if ess['variation'] else ''}": ess['fid']}
            for ess in essences_manager.layer.getFeatures(request)
        ]
        arbres_manager.fields.add_value_map('ESSENCE_ID', {'map': essences_list})

        # 2. Ensure "selected" field for secondary essences
        if "selected" not in [f.name() for f in essences_manager.layer.fields()]:
            essences_manager.fields.add_field("selected", QVariant.Bool)

        # 3. Mark secondary essences as selected
        excluded_codes = ", ".join([f"'{code}'" for code in codes])
        expression = f"code NOT IN ({excluded_codes})"
        essences_manager.fields.set_field_value_by_expression("selected", True, expression)

        # 4. Add value relation for ESSENCE_SECONDAIRE_ID
        config = {
            'FilterExpression': '"selected" = True',
            'Key': 'fid',
            'Layer': essences_manager.layer.id(),
            'Value': 'essence_variation',
            'AllowNull': True
        }
        arbres_manager.fields.add_value_relation('ESSENCE_SECONDAIRE_ID', config)

        # 5. Constrain ESSENCE_ID & ESSENCE_SECONDAIRE_ID
        ess_expr = """
        ((COALESCE("ESSENCE_ID", '') <> '') AND "ESSENCE_SECONDAIRE_ID" IS NULL)
        OR
        ((COALESCE("ESSENCE_ID", '') = '') AND "ESSENCE_SECONDAIRE_ID" IS NOT NULL)
        """
        msg = "Veuillez sélectionner une valeur pour ESSENCE ou ESSENCE_SECONDAIRE (mais pas les deux)."
        arbres_manager.fields.set_constraint_expression('ESSENCE_ID', ess_expr, msg, QgsFieldConstraints.ConstraintStrengthHard)

    @staticmethod
    def configure_aliases(layer_manager):
        aliases = [
            ("ID_CODE", "CODE"),
            ("ESSENCE_ID", "ESSENCE"),
            ("ESSENCE_SECONDAIRE_ID", "ESSENCE SECONDAIRE"),
            ("FAVORI", "⭐"),
            ("COMPTEUR", "ID")]
        
        for field, alias in aliases:
            layer_manager.fields.set_alias(field, alias)

    @staticmethod
    def configure_fid(layer_manager):
        layer_manager.fields.set_default_value("fid", 'if (maximum("fid") is NULL, 1 ,maximum("fid") + 1)')

    @staticmethod
    def configure_uuid(layer_manager):
        field_name = "UUID"
        layer_manager.fields.set_constraint(field_name, QgsFieldConstraints.ConstraintUnique)
        layer_manager.fields.set_default_value(field_name, "uuid()")
        layer_manager.fields.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)

    @staticmethod
    def configure_compteur(layer_manager):
        field_name = "COMPTEUR"
        layer_manager.fields.set_read_only(field_name)
        layer_manager.fields.set_default_value(field_name, 'count("fid") + 1')

    @staticmethod
    def configure_parcelle(layer_manager):
        field_name = "PARCELLE"
        layer_manager.fields.set_reuse_last_value(field_name)
        layer_manager.fields.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)

    @staticmethod
    def configure_diametre(layer_manager, dmin, dmax):
        field_name = "DIAMETRE"
        layer_manager.fields.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        layer_manager.fields.add_value_map(field_name, {'map': [{str(d): str(d)} for d in range(dmin, dmax, 5)]})
        layer_manager.fields.set_constraint_expression(
            field_name,
            '"DIAMETRE" != \'\'',
            "Le champ DIAMETRE ne peut pas être vide.", 
            QgsFieldConstraints.ConstraintStrengthHard
            )

    @staticmethod
    def configure_hauteur(layer_manager, hmin, hmax):
        field_name = "HAUTEUR"
        layer_manager.fields.add_value_map(field_name, {'map': [{str(h): str(h)} for h in range(hmin, hmax)]})

    @staticmethod
    def configure_effectif(layer_manager):
        field_name = "EFFECTIF"
        layer_manager.fields.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        layer_manager.fields.add_range('EFFECTIF', {'AllowNull': False, 'Max': 1000, 'Min': 0, 'Precision': 0, 'Step': 1})
        layer_manager.fields.set_default_value("EFFECTIF", '1', False)

    @staticmethod
    def configure_observation(layer_manager):
        field_name = "OBSERVATION"
        observation_choices = ["Chablis", "Bio", "Ehouppé", "Cablage"]
        layer_manager.fields.add_value_map(field_name, {'map': [{v: v} for v in observation_choices]})

    @staticmethod
    def configure_favori(layer_manager):
        layer_manager.fields.set_default_value("FAVORI", "FALSE")

    @staticmethod
    def configure_fid_code(layer_manager):
        field_name = "ID_CODE"
        layer_manager.fields.set_read_only(field_name)
        layer_manager.fields.set_default_value(
            field_name,
            """
            WITH_VARIABLE(
                'ess',
                get_feature(
                    'essences',
                    'fid',
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
            """
        )

    @staticmethod
    def configure_labelling(arbres_manager):
        label_settings = QgsPalLayerSettings()
        label_settings.fieldName = "COMPTEUR"
        text_format = QgsTextFormat()
        text_format.setFont(QFont("Arial", 12))
        text_format.setSize(12)
        label_settings.setFormat(text_format)
        labeling = QgsVectorLayerSimpleLabeling(label_settings)
        arbres_manager.layer.setLabeling(labeling)
        arbres_manager.layer.setLabelsEnabled(True)
        arbres_manager.layer.triggerRepaint()

    def create_tree_marking(self, codes, dmin, dmax, hmin, hmax):

        # 1. Create base geopackage
        arbre_layer = self.create_arbres_layer()
        essence_layer = self.essences_layer

        params = {'LAYERS': [arbre_layer, essence_layer], 'OUTPUT': get_path("inventaire"), 'OVERWRITE': True,}
        processing.run("native:package", params)

        add_layers_from_gpkg(get_path("inventaire"), "essences", "arbres")

        # Load layers using LayerManager
        arbres_manager = LayerManager("arbres")
        essences_manager = LayerManager("essences")

        self.configure_form(arbres_manager)
        
        self.configure_aliases(arbres_manager)

        self.configure_essence_field(arbres_manager, essences_manager, codes)

        self.configure_fid(arbres_manager)
        self.configure_uuid(arbres_manager)
        self.configure_compteur(arbres_manager)
        self.configure_parcelle(arbres_manager)
        self.configure_diametre(arbres_manager, dmin, dmax)
        self.configure_hauteur(arbres_manager, hmin, hmax)
        self.configure_effectif(arbres_manager)
        self.configure_observation(arbres_manager)
        self.configure_favori(arbres_manager)
        self.configure_fid_code(arbres_manager)

        self.configure_labelling(arbres_manager)

        # QField-specific sync setting
        arbres_manager.layer.setCustomProperty("QFieldSync/value_map_button_interface_threshold", 99)

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
                        pass  # Style is optional

                    QgsProject.instance().addMapLayer(layer)

                except Exception as e:
                    QMessageBox.warning(
                        self, "Erreur de chargement",
                        f"Impossible de charger {logical_key} : {str(e)}"
                    )

    def package_for_qfield_and_zip(self):
        """
        Packages the current QGIS project for QField, zips the result,
        and saves the zip file to `zip_output_path`.
        """
        project = QgsProject.instance()
        offline_editing = QgsOfflineEditing()
        export_path = get_path("inv_qfield")

        # Create a temp folder for the QField package
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Full path to .qgs file inside the package
            project_file_path = os.path.join(tmp_dir, f"{project.baseName()}.qgs")

            dialog = PackageDialog(self.iface, project, offline_editing)
            dialog.packagedProjectFileWidget.setFilePath(project_file_path)
            dialog.packagedProjectTitleLineEdit.setText(project.baseName())
            dialog._validate_packaged_project_filename()
            dialog.package_project()

            # Zip the temp folder contents into a single zip file
            zip_folder_contents(tmp_dir, export_path)

        print(f"✅ Project packaged successfully for QField at: {export_path}")
