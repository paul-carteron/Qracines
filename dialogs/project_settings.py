from pathlib import Path

from qgis.PyQt.QtWidgets import QDialog, QFileDialog
from qgis.core import Qgis, QgsProject
from qgis.utils import iface
from .project_settings_dialog import Ui_ProjectSettingsDialog

# Import from utils folder
from ..utils.variable_utils import (
    get_project_variable, 
    set_project_variable, 
    get_formated_surface, 
    get_grouped_values_from_shapefile, 
    sum_surface_from_shapefile,
    clear_project,
    )
from ..utils.layer_utils import load_wms, load_vectors, zoom_on_layer, create_map_theme, replier
from ..utils.path_manager import get_racines_path, get_path, get_wms

class ProjectSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.ui = Ui_ProjectSettingsDialog()
        self.ui.setupUi(self)

        # Liste des projets possibles
        projects = ["SITUATION", "ASSEMBLAGE", "PEUPLEMENTS", "GEOLOGIE", "ENJEUX"]

        cb = self.ui.comboBox_projects
        cb.addItem("") 
        cb.addItems(projects)
        cb.setCurrentIndex(0)
        
        # Charger les paramètres existants
        self.load_settings()

        # Connecter les boutons
        self.ui.buttonBox.accepted.connect(self.save_settings)
        self.ui.pushButton.clicked.connect(self.select_directory)

        # Connection des checkboxes
        self.nom_checkbox = {
            self.ui.checkBox_domaine: "Domaine",
            self.ui.checkBox_massif: "Massif",
            self.ui.checkBox_foret: "Forêt",
            self.ui.checkBox_bois: "Bois",
        }
        for cb in self.nom_checkbox:
            cb.toggled.connect(self.update_forest_name)

        self.ui.pushButton_refresh.clicked.connect(self.fill_in_cartouche)

    def load_settings(self):
        self.ui.lineEdit_directory.setText(get_project_variable("forest_directory") or "")
        self.ui.lineEdit_prefixe.setText(get_project_variable("forest_prefix") or "")
        self.ui.lineEdit_name.setText(get_project_variable("forest_name") or "")
        self.ui.lineEdit_city.setText(get_project_variable("forest_city") or "")
        self.ui.lineEdit_owner.setText(get_project_variable("forest_owner") or "")
        self.ui.doubleSpinBox.setValue(get_project_variable("forest_surface") or 0)
        self.ui.comboBox_projects.setCurrentText(get_project_variable("forest_map_project") or "")

    def save_settings(self):
      
        # Récupère les paramètres
        directory = self.ui.lineEdit_directory.text()
        prefix = self.ui.lineEdit_prefixe.text()
        name = self.ui.lineEdit_name.text()
        city = self.ui.lineEdit_city.text()
        owner = self.ui.lineEdit_owner.text()
        surface = self.ui.doubleSpinBox.value()
        formated_surface = get_formated_surface(surface * 10000)
        map_project = self.ui.comboBox_projects.currentText()
       
        # Sauvegarder les paramètres
        set_project_variable("forest_directory", directory)
        set_project_variable("forest_prefix", prefix)
        set_project_variable("forest_name", name)
        set_project_variable("forest_city", city)
        set_project_variable("forest_owner", owner)
        set_project_variable("forest_map_project", map_project)
        set_project_variable("forest_surface", surface)
        set_project_variable("forest_formated_surface", formated_surface)

        # Lance la création de la map
        self.create_map_project(map_project)
        self.save_current_project(map_project)

    def select_directory(self):
        # directory is the path to "123456_FORET"
        default_path = get_racines_path("cartographie") / "2_FORETS"
        self.directory = QFileDialog.getExistingDirectory(self, "Sélectionner…", str(default_path))
        if not self.directory:
            return
        
        self.fill_in_cartouche()
    
    def fill_in_cartouche(self):
        # Compute key paths
        prefix = self._get_prefix_from_directory(self.directory)
        parca_path = get_path("parca_polygon", prefix, self.directory)
        ua_path = get_path("ua_polygon", prefix, self.directory)

        # fill in cartouche
        self._set_directory_and_prefix(self.directory, prefix)
        self._set_name(prefix)
        self._set_city_and_owner(parca_path)
        self._set_surface(ua_path, parca_path)
        
    @staticmethod
    def _get_prefix_from_directory(path):
        """
        Récupère la partie avant le premier '_' dans le nom du dossier.
        Si aucun '_' n'est trouvé, renvoie une chaîne vide.
        """
        name = Path(path).name
        prefix, sep, suffix = name.partition("_")
        return suffix if sep else prefix


    def _set_directory_and_prefix(self, directory, prefix):
        self.ui.lineEdit_directory.setText(directory)
        set_project_variable("forest_directory", directory)

        self.ui.lineEdit_prefixe.setText(prefix)
        set_project_variable("forest_prefix", prefix)

    def _set_name(self, prefix):
        self.name = prefix.title() if prefix else ""
        self.ui.lineEdit_name.setText(self.name)
        set_project_variable("forest_name", self.name)

    def _set_city_and_owner(self, parca_path):
        city = owner = ""
        if parca_path.exists():
            city = get_grouped_values_from_shapefile(parca_path, "COM_NOM", "DEP_CODE", "SURF_CA")
            owner = get_grouped_values_from_shapefile(parca_path, "PROP", None, "SURF_CA")

        self.ui.lineEdit_city.setText(city)
        set_project_variable("forest_city", city)

        self.ui.lineEdit_owner.setText(owner)
        set_project_variable("forest_owner", owner)

    def _set_surface(self, ua_path, parca_path):
        if ua_path.exists():
            surface = sum_surface_from_shapefile(ua_path, "SURF_COR", "OCCUP_SOL", "BOISEE")
        elif parca_path.exists():
            surface = sum_surface_from_shapefile(parca_path, "SURF_CA")
        else:
            surface = 0

        self.ui.doubleSpinBox.setValue(surface)
        set_project_variable("forest_surface", surface)

    def update_forest_name(self):

        base = self.name or get_project_variable("forest_name") or ""

        # find the first‐checked box (if any) and grab its label
        prefix = next((label for cb, label in self.nom_checkbox.items() if cb.isChecked()), "")

        if prefix and base:
            # plural names take " des "
            if base.lower().endswith("s"):
                connector = " des "
            # then vowel or mute-h → d'
            elif base[0].lower() in ("a","e","i","o","u","h"):
                connector = " d'"
            # otherwise normal " de "
            else:
                connector = " de "
            full = f"{prefix}{connector}{base}"
        else:
            full = base
            
        self.ui.lineEdit_name.setText(full)
      
    def save_current_project(self, map_project):
        if self.ui.checkBox_saved.isChecked():
            project = QgsProject.instance()
            save_path = get_path(map_project.lower(), self.name, self.directory)
            project.write(save_path)
            
    def create_map_project(self, map_project):

        clear_project()
        # I can massively DRY up this part be create a project_factory with a method create_map_project but it's working for now

        if map_project == 'SITUATION':
            # zoom_on_layer should be called before loading wms
            load_vectors("ua_polygon_occup", "prop_polygon", "prop_point", "prop_line", "infra_point_acces", "coms_point", "coms_line", "parca_polygon_legend")
            zoom_on_layer("parca_polygon_legend")

            load_wms("scan25", "scan1000", group_name = "RASTER")

            map_themes = [("1_SCAN25_all",
                            ['prop_polygon', 'infra_point_acces', 'coms_point', 'coms_line', 'scan25'],
                            ['ua_polygon_occup', 'prop_point', 'prop_line', 'parca_polygon_legend', 'scan1000']),
                          ("2_SCAN25_boisee",
                            ['ua_polygon_occup', 'prop_line', 'infra_point_acces', 'coms_point', 'coms_line', 'scan25'], 
                            ['prop_polygon', 'prop_point', 'parca_polygon_legend', 'scan1000']),
                          ("3_SCAN1000",
                            ['prop_point', 'scan1000'],
                            ['ua_polygon_occup', 'prop_polygon', 'prop_line', 'infra_point_acces', 'coms_point', 'coms_line', 'parca_polygon_legend', 'scan25'])]
            for theme in map_themes:
                create_map_theme(*theme)
            

            self.iface.messageBar().pushMessage("QSequoia2", f"Projet {map_project} généré avec succès", level=Qgis.Success, duration=10)
          
        if map_project == 'ASSEMBLAGE':
            # zoom_on_layer should be called before loading wms
            load_vectors(
                'ua_polygon_occup', 'parca_polygon_occup', 'parca_polygon', 'prop_line', 'road_polygon', 'road_line', 'lieudit_point', 
                'infra_point', 'infra_polygon', 'infra_line', 'com_point', 'com_line', 'parca_polygon_legend'
            )
            zoom_on_layer("parca_polygon_legend")

            load_wms("scan25_grey", "scan100", "scan1000", "pci", "irc", "rgb", group_name="RASTER")
            
            # little customization
            wms_display_name,_ = get_wms("scan25_grey")
            layer = QgsProject.instance().mapLayersByName(wms_display_name)[0]
            layer.setOpacity(0.5)

            
            map_themes = [("1_Vector_all",
                            ['parca_polygon', 'prop_line', 'road_polygon', 'road_line', 'lieudit_point', 'infra_point', 'infra_polygon', 'infra_line', 'com_point', 'com_line'],
                            ['ua_polygon_occup', 'parca_polygon_occup', 'parca_polygon_legend', 'scan25_grey', 'scan100', 'scan1000', 'irc', 'rgb', 'pci']),
                          ("2_Vector_boisee",
                            ['ua_polygon_occup', 'parca_polygon_occup', 'prop_line', 'road_polygon', 'road_line', 'lieudit_point', 'infra_point', 'infra_polygon', 'infra_line', 'com_point', 'com_line'],
                            ['parca_polygon', 'parca_polygon_legend', 'scan25_grey', 'scan100', 'scan1000', 'irc', 'rgb', 'pci']),
                          ("3_Raster_all",
                            ['parca_polygon', 'prop_line', 'road_polygon', 'road_line', 'lieudit_point', 'infra_point', 'infra_polygon', 'infra_line', 'com_point', 'com_line', 'scan25_grey'],
                            ['ua_polygon_occup', 'parca_polygon_occup', 'parca_polygon_legend', 'scan100', 'scan1000', 'irc', 'rgb', 'pci']),
                          ("4_Raster_boisee",
                            ['ua_polygon_occup', 'parca_polygon_occup', 'prop_line', 'road_polygon', 'road_line', 'lieudit_point', 'infra_point', 'infra_polygon', 'infra_line', 'com_point', 'com_line', 'scan25_grey'],
                            ['parca_polygon', 'parca_polygon_legend', 'scan100', 'scan1000', 'irc', 'rgb', 'pci'])]
            for theme in map_themes:
                create_map_theme(*theme)

            replier()      

            self.iface.messageBar().pushMessage("QSequoia2", f"Projet {map_project} généré avec succès", level=Qgis.Success, duration=10)
            
        if map_project == 'PEUPLEMENTS':
            # zoom_on_layer should be called before loading wms
            load_vectors(
                'ua_polygon_ame', 'ua_polygon_occup', 'ua_polygon_plt', 'ua_polygon', 'parca_polygon_occup', 'sspf_polygon_plt', 'sspf_polygon', 
                'pf_polygon', 'pf_line', 'prop_line', 'route_polygon', 'route_line', 'lieudit_point', 'infra_point', 'infra_polygon', 'infra_line', 
                'com_point', 'com_line', 'parca_polygon_legend'
            )
            zoom_on_layer("parca_polygon_legend")

            load_wms("scan25_grey", "scan100", "scan1000", "pci", "irc", "rgb", group_name="RASTER")
            # little customization
            wms_display_name,_ = get_wms("scan25_grey")
            layer = QgsProject.instance().mapLayersByName(wms_display_name)[0]
            layer.setOpacity(0.5)

            map_themes = [("0_work",
                            ['ua_polygon', 'parca_polygon_occup', 'prop_line', 'route_polygon', 'route_line', 'irc'],
                            ['ua_polygon_ame', 'ua_polygon_occup', 'ua_polygon_plt', 'sspf_polygon', 'pf_polygon', 'pf_line', 'lieudit_point', 'infra_point', 
                             'infra_polygon', 'infra_line', 'com_point', 'com_line', 'parca_polygon_legend', 'scan25_grey', 'scan100', 'scan1000', 'rgb', 'pci']),
                          ("1_Vector_plt",
                            ['sspf_polygon_plt', 'sspf_polygon', 'pf_polygon', 'pf_line', 'prop_line', 'route_polygon', 'route_line', 'lieudit_point', 'infra_point', 
                             'infra_polygon', 'infra_line', 'com_point', 'com_line'],
                            ['ua_polygon_ame', 'ua_polygon_occup', 'ua_polygon_plt', 'ua_polygon', 'parca_polygon_occup', 'parca_polygon_legend', 'scan25_grey', 
                             'scan100', 'scan1000', 'irc', 'rgb', 'pci']),
                          ("2_Vector_ame",
                            ['ua_polygon_ame', 'sspf_polygon', 'pf_polygon', 'pf_line', 'prop_line', 'route_polygon', 'route_line', 'lieudit_point', 'infra_point', 
                             'infra_polygon', 'infra_line', 'com_point', 'com_line'],
                            ['ua_polygon_occup', 'ua_polygon_plt', 'ua_polygon', 'parca_polygon_occup', 'sspf_polygon_plt', 'parca_polygon_legend', 'scan25_grey', 
                             'scan100', 'scan1000', 'irc', 'rgb', 'pci']),
                          ("3_Raster_plt",
                            ['sspf_polygon_plt', 'sspf_polygon', 'pf_polygon', 'pf_line', 'prop_line', 'route_polygon', 'route_line', 'lieudit_point', 'infra_point', 
                             'infra_polygon', 'infra_line', 'com_point', 'com_line', 'scan100'],
                            ['ua_polygon_ame', 'ua_polygon_occup', 'ua_polygon_plt', 'ua_polygon', 'parca_polygon_occup', 'parca_polygon_legend', 'scan25_grey', 
                             'scan1000', 'irc', 'rgb', 'pci']),
                          ("4_Raster_ame",
                            ['ua_polygon_ame', 'sspf_polygon', 'pf_polygon', 'pf_line', 'prop_line', 'route_polygon', 'route_line', 'lieudit_point', 'infra_point', 
                             'infra_polygon', 'infra_line', 'com_point', 'com_line', 'scan100'],
                            ['ua_polygon_occup', 'ua_polygon_plt', 'ua_polygon', 'parca_polygon_occup', 'sspf_polygon_plt', 'parca_polygon_legend', 'scan25_grey', 
                             'scan1000', 'irc', 'rgb', 'pci'])]
            
            for theme in map_themes:
                create_map_theme(*theme)

            replier()  

            self.iface.messageBar().pushMessage("QSequoia2", f"Projet {map_project} généré avec succès", level=Qgis.Success, duration=10)
            
        if map_project == 'GEOLOGIE':
            # zoom_on_layer should be called before loading wms
            load_vectors('geol_polygon', 'ua_polygon', 'pf_polygon', 'pf_line', 'prop_line', 'parca_polygon_legend')
            zoom_on_layer("parca_polygon_legend")

            load_wms("geol")

            map_themes = [("0_Geol",
                            ['geol_polygon', 'parca_polygon_occup', 'pf_polygon', 'pf_line', 'prop_line', "geol"],
                            ['ua_polygon', 'parca_polygon_legend'])]
            
            for theme in map_themes:
                create_map_theme(*theme)

            replier()
            
            self.iface.messageBar().pushMessage("QSequoia2", f"Projet {map_project} généré avec succès", level=Qgis.Success, duration=10)
            
        if map_project == 'ENJEUX':
            # zoom_on_layer should be called before loading wms
            load_vectors('pf_polygon', 'pf_line', 'prop_line', 'parca_polygon_legend')
            zoom_on_layer("parca_polygon_legend")

            load_wms("scan25_grey")
            # little customization
            wms_display_name, _ = get_wms("scan25_grey")
            layer = QgsProject.instance().mapLayersByName(wms_display_name)[0]
            layer.setOpacity(0.5)
            
            map_themes = [("1_Enjeux",
                            ['pf_polygon', 'pf_line', 'prop_line', 'scan25_grey'],
                            ['parca_polygon_legend'])]
            for theme in map_themes:
                create_map_theme(*theme)

            replier()
            
            self.iface.messageBar().pushMessage("QSequoia2", f"Projet {map_project} généré avec succès", level=Qgis.Success, duration=10)
