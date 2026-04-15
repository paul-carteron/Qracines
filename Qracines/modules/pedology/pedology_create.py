from qgis.core import QgsProcessing
from qgis.PyQt.QtWidgets import QDialog, QMessageBox
from qgis.core import QgsProject

from .pedology_dialog import Ui_PedologyCreateDialog

from ...utils.config import get_guides, get_style, get_stations, get_racines_path
from ...utils.layers import load_vectors, load_gpkg, create_relation
from ...utils.utils import clear_project
from ...utils.ui import RasterController, QfieldPackager

from ...core.layer.factory import LayerFactory

import processing

class PedologyCreateDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.ui = Ui_PedologyCreateDialog()
        self.ui.setupUi(self)
        self.iface = iface
        self.project = QgsProject.instance()
        
        # --- initialize from helpers class ---
        raster_checkbox = {
            #   'key':     'checkbox_name',
                'plt_anc': 'cb_plt_anc',
                'plt':     'cb_plt',
                'mnh':     'cb_mnh',
                'scan25':  'cb_scan25',
                'irc':     'cb_irc',
                'rgb':     'cb_rgb',
            }
        self.raster_controller = RasterController(ui=self.ui, raster_checkbox=raster_checkbox)
        

        self.packager = QfieldPackager(
            self.ui,
            default_dir = get_racines_path("expertise", "Qfield", "Pedology"),
            package_ui = 'cb_package_for_qfield',
            outdir_ui = 'fw_outdir'
            )
        
        # --- Populate cob_stations with guides ---
        guides = get_guides()
        self.ui.cob_stations.addItems(guides)

    def create_pedology(self):
        guide = self.ui.cob_stations.currentText()
        stations = get_stations(guide)
           
        layers = [LayerFactory.create("sondage", "PEDOLOGY"), LayerFactory.create("horizons", "PEDOLOGY")]

        result = processing.run("native:package", {
            'LAYERS':      layers,
            'OUTPUT':      QgsProcessing.TEMPORARY_OUTPUT,
            'OVERWRITE':   True,
            'SAVE_STYLES': False
        })

        self.gpkg_path = result['OUTPUT']
        load_gpkg(self.gpkg_path, group_name="PEDOLOGY")

        # Création de la relation
        create_relation('sondage', 'horizons', 'uuid', 'sondage', 'sondage_horizons','sondage')
        
        # Application du style aux couches créées
        for key in ("sondage", "horizons"):
            layers = self.project.mapLayersByName(key)
            if not layers:
                continue
            layer = layers[0]
            style_path = get_style(key)
            if layer.loadNamedStyle(str(style_path)):
                layer.triggerRepaint()

        sondage_mgr = LayerManager('sondage')
        sondage_mgr.fields.add_value_map('station', {'map': [{str(s): str(s)} for s in stations]})

    def accept(self):
        
        clear_project()

        try:
            self.create_pedology()
            load_vectors("ua_polygon", group_name= "VECTEUR")
            self.raster_controller.load_selected_rasters()

            msg = "Projet pedologique terminé !"
            if self.packager.is_valid():
                packaged_dir = self.packager.package(prefix="PEDO")
                msg += f"\nProjet packagé dans :\n{packaged_dir}"

            QMessageBox.information(self, "Succès", msg)

            super().accept()

        except Exception as e:
            # everything else bubbles up here
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue :\n{e}")