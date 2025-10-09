from pathlib import Path
import processing

from qgis.core import QgsProject, QgsVectorLayer, QgsFieldConstraints, QgsProcessing

from qgis.utils import iface

from ..core.layer_factory import LayerFactory
from ..core.db.manager import DatabaseManager
from ..core.layer.manager import LayerManager
from ..utils.config import get_path, get_style
from ..utils.layers import load_gpkg, load_vectors, load_rasters, create_relation
from ..utils.utils import zoom_on, create_theme


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
        outdir: Path,
        title: str,
        dmin: int,
        dmax: int,
        hmin: int,
        hmax: int,
        raster_choices: dict[str, bool]
    ):
        self.iface = iface
        self.project = QgsProject.instance()
        self.root = self.project.layerTreeRoot()
        self.outdir = outdir
        self.title = title
        self.dmin, self.dmax = dmin, dmax
        self.hmin, self.hmax = hmin, hmax
        self.raster_choices = raster_choices
        self.essences_layer = DatabaseManager().load_essences("Ess")
        self.parcelles: set[str] | None = None

    def run_full_diagnostic(self):

        self._create_and_load_gpkg()
        self._load_and_style_vectors()
        load_vectors("parca_polygon_occup", group_name= "VECTOR")
        self._load_and_style_rasters()        
        self._create_themes()
        self._create_relations()
        self._apply_styles()
        self._configure_layers()

    def _load_parcellaire(self):
        path = get_path("parcellaire")
        if not path.exists():
            return None

        layer = QgsVectorLayer(str(path), "Parcellaire", "ogr")
        if not layer.isValid():
            return None

        # collect unique parcel IDs
        self.parcelles = {feat["PARCELLE"] for feat in layer.getFeatures()}
        return layer

    def _create_and_load_gpkg(self):
        # Create memory layers
        names = ["Placette", "Transect", "Limite", "Picto", "Gha", "Tse", "Reg", "Va_ess"]
        layers = [LayerFactory.create(name, "DIAGNOSTIC") for name in names]
        layers.append(self.essences_layer)
        parc = self._load_parcellaire()
        if parc:
            layers.append(parc)

        result = processing.run("native:package", {
            'LAYERS':      layers,
            'OUTPUT':      QgsProcessing.TEMPORARY_OUTPUT,
            'OVERWRITE':   True,
            'SAVE_STYLES': False
        })

        self.gpkg_path = result['OUTPUT']

        load_gpkg(self.gpkg_path, group_name="DIAGNOSTIC")

    def _load_and_style_vectors(self):
        load_vectors("prop_line", "prop_diag_line", "pf_line", "pf_diag_line", "ua_polygon", group_name= "VECTOR")
        zoom_on("ua_polygon")

    def _load_and_style_rasters(self):
        keys = [key for key, cb in self.raster_choices.items() if cb.isChecked()]
        if keys:
            load_rasters(*keys, group_name="RASTER")

    def _create_themes(self):
        always_visible = ['Placette', 'Transect', 'Picto', 'Limite']
        themes = [
            ("1_plt", always_visible + ['plt', 'prop_line', 'pf_line', 'ua_polygon']),
            ("2_plt_anc", always_visible +['plt_anc', 'prop_line', 'pf_line']),
            ("3_irc", always_visible + ['irc', 'prop_diag_line', 'pf_diag_line', 'ua_polygon']),
            ("4_rgb", always_visible + ['rgb', 'prop_diag_line', 'pf_diag_line', 'ua_polygon']),
            ("5_mnh", always_visible + ['mnh', 'prop_line', 'pf_line', 'ua_polygon']),
            ("6_scan25", always_visible + ['scan25', 'prop_line', 'pf_line', 'ua_polygon']),
        ]
        for theme in themes:
            create_theme(*theme)

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
            if layer.loadNamedStyle(str(style_path)):
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
            {'map': [{str(d): str(d)} for d in range(self.dmin, self.dmax + 1, 5)]}
        )
        transect_mgr.fields.add_value_map(
            'TR_HAUTEUR',
            {'map': [{str(h): str(h)} for h in range(self.hmin, self.hmax + 1)]}
        )
        if self.parcelles:
            transect_mgr.fields.add_value_map(
                'PLTM_PARC',
                {'map': [{str(p): str(p)} for p in self.parcelles]}
            )

        # Va_ess
        va_mgr = LayerManager('Va_ess')
        va_mgr.forms.init_drag_and_drop_form()
        va_mgr.forms.add_fields_to_tab('VA_ESS','VA_STADE','VA_AGE_APP','VA_HT','VA_ELAG','VA_TX_HA','CUMUL_TX_VA')
        # set hard/soft constraints and defaults as needed
        va_mgr.fields.set_constraint('VA_TX_HA', QgsFieldConstraints.ConstraintNotNull)