from pathlib import Path
import os, tempfile, shutil

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsFieldConstraints,
    QgsOfflineEditing
)
from qgis.utils import iface
import processing
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QCoreApplication

from ..core.layer_factory import LayerFactory
from ..core.db.manager import DatabaseManager
from ..core.layer.manager import LayerManager
from ..utils.path_manager import get_path, get_style, find_similar_filenames
from ..utils.qfield_utils import zip_folder_contents, add_layers_from_gpkg, create_relation
from ..utils.layer_utils import create_map_theme

from ..utils.variable_utils import get_project_variable
from qfieldsync.gui.package_dialog import PackageDialog


class DiagnosticService:
    """
    Service class to perform the full diagnostic workflow:
      - Create in-memory layers and a GeoPackage
      - Load/style existing vector & raster data
      - Create map themes
      - Configure layer relations and forms
      - Package project for QField
    """

    def __init__(
        self,
        output_dir: Path,
        dmin: int,
        dmax: int,
        hmin: int,
        hmax: int,
        raster_choices: dict[str, bool]
    ):
        self.iface = iface
        self.project = QgsProject.instance()
        self.root = self.project.layerTreeRoot()
        self.output_dir = output_dir
        self.dmin, self.dmax = dmin, dmax
        self.hmin, self.hmax = hmin, hmax
        self.raster_choices = raster_choices
        self.essences_layer = DatabaseManager().load_essences("Ess")
        self.parcelles: set[str] | None = None

    def run_full_diagnostic(self):

        self._create_and_load_gpkg()
        self._load_and_style_vectors()
        self._load_and_style_rasters()
        self._create_map_themes()
        self._apply_styles()
        self._create_relations()
        self._configure_layers()
        self._package_for_qfield()

    def _load_parcellaire(self):
        path = get_path("parcellaire")
        if not os.path.exists(path):
            return None
        layer = QgsVectorLayer(path, "Parcellaire", "ogr")
        if not layer.isValid():
            return None
        # collect unique parcel IDs
        self.parcelles = {feat["PARCELLE"] for feat in layer.getFeatures()}
        return layer

    def _create_and_load_gpkg(self):
        # Create memory layers
        names = ["Placette", "Transect", "Limite", "Picto", "Gha", "Tse", "Reg", "Va_ess"]
        layers = [LayerFactory.create(name) for name in names]
        layers.append(self.essences_layer)
        parc = self._load_parcellaire()
        if parc:
            layers.append(parc)
        params = {
            'LAYERS': layers,
            'OUTPUT': get_path("diagnostic"),
            'OVERWRITE': True,
            'SAVE_STYLES': False
        }
        processing.run("native:package", params)
        add_layers_from_gpkg(get_path("diagnostic"))

    def _load_and_style_vectors(self):
        group = self.root.addGroup("Vector")
        vector_defs = [
            ("prop_line", "Limite de propriété b"),
            ("prop_diag_line", "Limite de propriété w"),
            ("ua_polygon", "Unité d analyse")
        ]
        for key, name in vector_defs:
            path = get_path(key)
            layer = QgsVectorLayer(path, name, "ogr")
            style_path = get_style(key)
            if layer.isValid():
                layer.setReadOnly(True)
                self.project.addMapLayer(layer, False)
                group.addLayer(layer)
                try:
                    layer.loadNamedStyle(style_path)
                    layer.triggerRepaint()
                except (FileNotFoundError, KeyError):
                    pass
            else:
                print(f"Failed to load vector layer: {name}")

    def _load_and_style_rasters(self):
        group = self.root.addGroup("Raster")

        for key, enabled in self.raster_choices.items():
            if not enabled:
                continue

            raster_path = get_path(key)
            if not os.path.exists(raster_path):
                sims = find_similar_filenames(raster_path, key)
                msg = f"Raster for {key} not found:\n{raster_path}"
                if sims:
                    msg += "\nSimilar files:\n" + "\n".join(sims)
                QMessageBox.information(None, "Raster missing", msg)
                continue

            layer = QgsRasterLayer(raster_path, key)
            if not layer.isValid():
                QMessageBox.warning(None, "Invalid raster", f"Could not load: {raster_path}")
                continue

            # --- Optional styling: ---
            style_path = None
            try:
                style_path = get_style(key)
            except (KeyError, ValueError, FileNotFoundError):
                pass

            if style_path:
                try:
                    layer.loadNamedStyle(style_path)
                    layer.triggerRepaint()
                except Exception as e:
                    # log failures without disturbing the user
                    QgsMessageLog.logMessage(
                        f"Failed to apply style for '{key}': {e}",
                        "Qsequoia2",
                        Qgis.Warning
                    )

            self.project.addMapLayer(layer, False)
            group.addLayer(layer)

    def _create_map_themes(self):
        themes = [
            ("1_plt",
             ['plt', 'Limite de propriété b', 'Limite de parcelle b', 'Unité d’analyse'],
             ['plt_anc', 'irc', 'rgb', 'mnh', 'scan25', 'Limite de propriété w', 'Limite de parcelle w']),
            ("2_plt_anc",
             ['plt_anc', 'Limite de propriété b', 'Limite de parcelle b'],
             ['plt', 'irc', 'rgb', 'mnh', 'scan25', 'Limite de propriété w', 'Limite de parcelle w', 'Unité d’analyse']),
            ("3_irc",
             ['irc', 'Limite de propriété w', 'Limite de parcelle w', 'Unité d’analyse'],
             ['plt', 'plt_anc', 'rgb', 'mnh', 'scan25', 'Limite de propriété b', 'Limite de parcelle b']),
            ("4_rgb",
             ['rgb', 'Limite de propriété w', 'Limite de parcelle w', 'Unité d’analyse'],
             ['plt', 'plt_anc', 'irc', 'mnh', 'scan25', 'Limite de propriété b', 'Limite de parcelle b']),
            ("5_mnh",
             ['mnh', 'Limite de propriété b', 'Limite de parcelle b', 'Unité d’analyse'],
             ['plt', 'plt_anc', 'irc', 'rgb', 'scan25', 'Limite de propriété w', 'Limite de parcelle w']),
            ("6_scan25",
             ['scan25', 'Limite de propriété b', 'Limite de parcelle b', 'Unité d’analyse'],
             ['plt', 'plt_anc', 'irc', 'rgb', 'mnh', 'Limite de propriété w', 'Limite de parcelle w'])
        ]
        for theme in themes:
            create_map_theme(*theme)

    def _apply_styles(self):
        name_key = [
            ('Placette', 'placette'),
            ('Transect', 'transect'),
            ('Picto', 'picto'),
            ('Limite', 'limite'),
            ('Gha', 'gha'),
            ('Tse', 'tse'),
            ('Reg', 'reg'),
            ('Va_ess', 'va_ess'),
        ]
        for layer_name, key in name_key:
            layers = self.project.mapLayersByName(layer_name)
            if not layers:
                continue
            layer = layers[0]
            style_path = get_style(key)
            if layer.loadNamedStyle(style_path):
                layer.triggerRepaint()

    def _create_relations(self):
        pairs = [
            ('Placette', 'Gha'),
            ('Placette', 'Tse'),
            ('Placette', 'Reg'),
            ('Placette', 'Va_ess')
        ]
        for parent, child in pairs:
            create_relation(
                parent, child,
                'PLACETTE', 'PLACETTE',
                f'{parent}_{child}',
                child
            )

    def _configure_layers(self):
        # Placette
        placette_mgr = LayerManager('Placette')
        placette_mgr.fields.set_constraint('PLACETTE', QgsFieldConstraints.ConstraintUnique)
        if self.parcelles:
            placette_mgr.fields.add_value_map(
                'PLTM_PARC',
                {'map': [{str(p): str(p)} for p in self.parcelles]}
            )

        # Transect
        transect_mgr = LayerManager('Transect')
        ## essences_types
        all_types = [feat["type"] for feat in self.essences_layer.getFeatures()]
        unique_types = list(dict.fromkeys(all_types))

        transect_mgr.fields.add_value_map(
            'TR_TYPE_ESS',
            {'map': [{str(t): str(t)} for t in unique_types]}
        )
        tr_ess_config = {
            'AllowMulti': False,
            'AllowNull': False,
            'Description': '',
            'FilterExpression': ' "type" = current_value(\'TR_TYPE_ESS\')',
            'Key': 'fid',
            'Layer': self.essences_layer.id(),
            'LayerName': self.essences_layer.name(),
            'NofColumns': 1,
            'OrderByValue': False,
            'UseCompleter': False,
            'Value': 'essence_variation'
        }
        transect_mgr.fields.add_value_relation('TR_ESS', tr_ess_config)


        transect_mgr.fields.add_value_map(
            'TR_DIAM',
            {'map': [{str(d): str(d)} for d in range(self.dmin, self.dmax, 5)]}
        )
        transect_mgr.fields.add_value_map(
            'TR_HAUTEUR',
            {'map': [{str(h): str(h)} for h in range(self.hmin, self.hmax)]}
        )
        if self.parcelles:
            transect_mgr.fields.add_value_map(
                'PLTM_PARC',
                {'map': [{str(p): str(p)} for p in self.parcelles]}
            )

        # Va_ess
        va_mgr = LayerManager('Va_ess')
        va_mgr.forms.init_drag_and_drop_form()
        va_mgr.forms.add_fields_to_tab([
            'VA_ESS','VA_STADE','VA_AGE_APP','VA_HT','VA_ELAG','VA_TX_HA','CUMUL_TX_VA'
        ])
        # set hard/soft constraints and defaults as needed
        va_mgr.fields.set_constraint('VA_TX_HA', QgsFieldConstraints.ConstraintNotNull)

    def _package_for_qfield(self):
        prefix = get_project_variable('forest_prefix')
        offline = QgsOfflineEditing()
        out_dir = self.output_dir

        if not out_dir.exists():
            QMessageBox.warning(None, "Missing output folder", "Please choose an output directory.")
            return

        # 1) Create a temp folder but don’t use the context manager
        tmp_dir = tempfile.mkdtemp()
        tmp_path = Path(tmp_dir)
        tmp_qgs  = tmp_path / f"{prefix}.qgs"

        try:
            # 2) Run the QFieldSync dialog to build the packaged project
            dlg = PackageDialog(iface, self.project, offline)
            dlg.packagedProjectFileWidget.setFilePath(str(tmp_qgs))
            dlg.packagedProjectTitleLineEdit.setText(self.project.baseName())
            dlg._validate_packaged_project_filename()
            dlg.package_project()

            # 3) Close & delete the dialog to drop file handles
            dlg.close()
            dlg.deleteLater()
            QCoreApplication.processEvents()

            # 4) Zip up the folder if you still want a .zip
            zip_path = out_dir / f"{prefix}.zip"
            try:
                zip_folder_contents(tmp_path, zip_path)
            except PermissionError:
                # swallow any locked‐file errors, since the .zip itself is valid
                pass

            QMessageBox.information(
                None,
                "Success",
                f"Project packaged for QField and zipped to:\n{zip_path}"
            )

        finally:
            # 5) Manually remove the temp dir, ignoring any leftover lock errors
            shutil.rmtree(tmp_path, ignore_errors=True)
