from PyQt5.QtWidgets import QDialog, QMessageBox
from qgis.PyQt import uic
from qgis.core import QgsProject, QgsCoordinateReferenceSystem
from PyQt5.QtCore import QTimer
from qgis.utils import iface

from .expertise_create_service import ExpertiseCreateService
from ....core.db.manager import DatabaseManager

from ....utils.config import get_racines_path
from ....utils.variable import get_project_variable
from ....utils.ui import RasterController, QfieldPackager, SpeciesSelector, GridController, DendroController

from pathlib import Path
FORM_CLASS, _ = uic.loadUiType(
    Path(__file__).parent / "expertise_create.ui")

class ExpertiseCreateDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.essences = DatabaseManager().load_essences("essences")
        self.seq_dir = get_project_variable("QS2_seq_dir") or None
        self.seq_id = get_project_variable("QS2_seq_id") or None
        
        self.dendro_controller = DendroController(
            ui = self,
            dendro_spinbox={
                'dmin': 'sp_dmin',
                'dmax': 'sp_dmax',
                'hmin': 'sp_hmin',
                'hmax': 'sp_hmax'
            }
        )

        self.raster_controller = RasterController(
            ui=self,
            raster_checkbox={
                #   'key':     'checkbox_name',
                'r.seq.mnh': 'cb_plt',
                'r.alt.mnh': 'cb_mnh',
                'r.scan.25': 'cb_scan25',
                'r.ortho.irc': 'cb_irc',
                'r.ortho.rgb': 'cb_rgb',
            })
        

        self.gha_tra_selector = SpeciesSelector(
            ui = self, layer = self.essences,
            choices="lw_species", selected="lw_selected_species",
            add="pb_add_species", remove="pb_remove_species",
            filter="le_filter_species"
        )

        self.tse_selector = SpeciesSelector(
            ui = self, layer = self.essences,
            choices="lw_species_taillis", selected="lw_selected_species_taillis",
            add="pb_add_species_taillis", remove="pb_remove_species_taillis",
            filter="le_filter_species_taillis"
        )
        tse_default = ["BOU", "CHA", "CHE", "ECH", "FRE", "HET", "NOI", "SAU", "TIL", "TRE"]
        tse_default_label = [name for name, code in self.tse_selector.essences_lookup.items() if code in tse_default]
        self.tse_selector.selected.addItems(tse_default_label)

        self.packager = QfieldPackager(
            self,
            default_dir = get_racines_path("expertise", "Qfield", "Expertise"),
            package_ui = 'cb_package_for_qfield',
            outdir_ui = 'fw_outdir'
            )
        
        self.grid_controller = GridController(
            self,
            create_grid_ui = 'cb_create_grid',
            points_per_ha_ui = 'dsp_points_per_ha'
        )

    def accept(self):

        if not self.gha_tra_selector.is_valid(): return
        if not self.tse_selector.is_valid(): return

        iface.actionNewProject().trigger()

        QTimer.singleShot(0, lambda: QgsProject.instance().setCrs(
            QgsCoordinateReferenceSystem("EPSG:2154")
        ))

        codes_gha_tra = self.gha_tra_selector.selected_codes()
        codes_taillis = self.tse_selector.selected_codes()

        svc = ExpertiseCreateService(
            seq_dir = self.seq_dir,
            codes = codes_gha_tra,
            codes_taillis = codes_taillis,
            dendro_controller = self.dendro_controller,
            grid_controller = self.grid_controller,
            raster_controller = self.raster_controller,
        )

        try:
            svc.run()

            msg = "Expertise complète !"
            if self.packager.is_valid():
                packaged_dir = self.packager.package(prefix="EXP", seq_id=self.seq_id, codes=codes_gha_tra)
                msg += f"\nProjet packagé dans :\n{packaged_dir}"
            QMessageBox.information(self, "Succès", msg)

            super().accept()

        except Exception as e:
            # everything else bubbles up here
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue :\n{e}")
