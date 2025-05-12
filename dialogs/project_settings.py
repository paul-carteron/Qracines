from qgis.PyQt.QtWidgets import QDialog, QFileDialog

from .project_settings_dialog import Ui_ProjectSettingsDialog

# Import from utils folder
from ..utils.variable_utils import (
    get_global_variable,
    get_project_variable, 
    set_project_variable, 
    get_prefix_from_directory, 
    get_formated_surface, 
    get_grouped_values_from_shapefile, 
    sum_surface_from_shapefile,
    clear_project,
    )
from ..utils.layer_utils import *
from ..utils.path_manager import get_racines_path, get_path

class ProjectSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
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
        prefix = get_prefix_from_directory(self.directory)
        parca_path = get_path("parca_polygon", prefix, self.directory)
        ua_path = get_path("ua_polygon", prefix, self.directory)

        # fill in cartouche
        self._set_directory_and_prefix(self.directory, prefix)
        self._set_name(prefix)
        self._set_city_and_owner(parca_path)
        self._set_surface(ua_path, parca_path)

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

        styles_directory = get_global_variable("styles_directory")
        forest_directory = get_project_variable("forest_directory")
        forest_prefix = get_project_variable("forest_prefix")

        if map_project == 'SITUATION':
            import_wms_from_config(["Scan25", "Scan1000"], group_name="RASTER")
            
            vector_layers = ['UA_polygon_OCCUP','PROP_polygon','PROP_point','PROP_line','INFRA_point_ACCES', 'COMS_point','COMS_line','PARCA_polygon_LEGEND']
            import_vectors_from_config(styles_directory, forest_directory, "new_directories", forest_prefix, vector_layers)
            
            zoom_on_layer("Légende")
            
            map_themes = [("1_SCAN25_all",
                            ['Propriété', 'INFRA_point', 'COMS_point', 'COMS_line', 'IGN SCAN 25 TOPO (Metropole)'],
                            ['Occupation du sol', 'Centroid de propriété', 'Limite de propriété', 'Légende', 'IGN SCAN 1000 TOPO (Metropole)']),
                          ("2_SCAN25_boisee",
                            ['Occupation du sol', 'Limite de propriété', 'INFRA_point', 'COMS_point', 'COMS_line', 'IGN SCAN 25 TOPO (Metropole)'], 
                            ['Propriété', 'Centroid de propriété', 'Légende', 'IGN SCAN 1000 TOPO (Metropole)']),
                          ("3_SCAN1000",
                            ['Centroid de propriété', 'IGN SCAN 1000 TOPO (Metropole)'],
                            ['Occupation du sol', 'Propriété', 'Limite de propriété', 'INFRA_point', 'COMS_point', 'COMS_line', 'Légende', 'IGN SCAN 25 TOPO (Métropole)'])]
            for theme in map_themes:
                create_map_theme(*theme)
                
            self.iface.messageBar().pushMessage("QSequoia2", "SITUATION généré avec succès", level=Qgis.Success, duration=10)
          
        if map_project == 'ASSEMBLAGE':
            import_wms_from_config(["Scan25_gray", "Scan100", "Scan1000", "PCI", "IRC", "RGB"], group_name="RASTER")
            customize('IGN SCAN 25 TOPO (Metropole) gray')
            
            vector_layers = ['UA_polygon_OCCUP', 'PARCA_polygon_OCCUP', 'PARCA_polygon', 'PROP_line', 'ROAD_polygon', 'ROAD_line', 'LIEUDIT_point', 'INFRA_point', 'INFRA_polygon', 'INFRA_line', 'COM_point', 'COM_line', 'PARCA_polygon_LEGEND']
            import_vectors_from_config(styles_directory, forest_directory, "new_directories", forest_prefix, vector_layers)
            
            zoom_on_layer("Légende")
            replier()
            
            map_themes = [("1_Vector_all",
                            ['Parcelle cadastrale', 'Limite de propriété', 'ROAD_polygon', 'ROAD_polygon', 'ROAD_line', 'LIEUDIT_point', 'INFRA_point', 'INFRA_polygon', 'INFRA_line', 'COM_point', 'COM_line'],
                            ['Occupation du sol', 'Parcelle cadastrale *', 'Légende', 'IGN SCAN 25 TOPO (Metropole) gray', 'IGN SCAN 100 TOPO (Metropole)', 'IGN SCAN 1000 TOPO (Metropole)', 'IGN BDORTHO IRC 20cm', 'IGN BDORTHO RGB 20cm', 'IGN Parcellaire Image']),
                          ("2_Vector_boisee",
                            ['Occupation du sol', 'Parcelle cadastrale *', 'Limite de propriété', 'ROAD_polygon', 'ROAD_polygon', 'ROAD_line', 'LIEUDIT_point', 'INFRA_point', 'INFRA_polygon', 'INFRA_line', 'COM_point', 'COM_line'],
                            ['Parcelle cadastrale', 'Légende', 'IGN SCAN 25 TOPO (Metropole) gray', 'IGN SCAN 100 TOPO (Metropole)', 'IGN SCAN 1000 TOPO (Metropole)', 'IGN BDORTHO IRC 20cm', 'IGN BDORTHO RGB 20cm', 'IGN Parcellaire Image']),
                          ("3_Raster_all",
                            ['Parcelle cadastrale', 'Limite de propriété', 'ROAD_polygon', 'ROAD_polygon', 'ROAD_line', 'LIEUDIT_point', 'INFRA_point', 'INFRA_polygon', 'INFRA_line', 'COM_point', 'COM_line', 'IGN SCAN 25 TOPO (Metropole) gray'],
                            ['Occupation du sol', 'Parcelle cadastrale *', 'Légende', 'IGN SCAN 100 TOPO (Metropole)', 'IGN SCAN 1000 TOPO (Metropole)', 'IGN BDORTHO IRC 20cm', 'IGN BDORTHO RGB 20cm', 'IGN Parcellaire Image']),
                          ("4_Raster_boisee",
                            ['Occupation du sol', 'Parcelle cadastrale *', 'Limite de propriété', 'ROAD_polygon', 'ROAD_polygon', 'ROAD_line', 'LIEUDIT_point', 'INFRA_point', 'INFRA_polygon', 'INFRA_line', 'COM_point', 'COM_line', 'IGN SCAN 25 TOPO (Metropole) gray'],
                            ['Parcelle cadastrale', 'Légende', 'IGN SCAN 100 TOPO (Metropole)', 'IGN SCAN 1000 TOPO (Metropole)', 'IGN BDORTHO IRC 20cm', 'IGN BDORTHO RGB 20cm', 'IGN Parcellaire Image'])]
            for theme in map_themes:
                create_map_theme(*theme)
            
            self.iface.messageBar().pushMessage("QSequoia2", "ASSEMBLAGE généré avec succès", level=Qgis.Success, duration=10)
            
        if map_project == 'PEUPLEMENTS':
            import_wms_from_config(["Scan25_gray", "Scan100", "Scan1000", "PCI", "IRC", "RGB"], group_name="RASTER")
            customize('IGN SCAN 25 TOPO (Metropole) gray')
            
            vector_layers = ['UA_polygon_AME', 'UA_polygon_OCCUP', 'UA_polygon_PLT', 'UA_polygon', 'PARCA_polygon_OCCUP', 'SSPF_polygon_PLT', 'SSPF_polygon', 'PF_polygon', 'PF_line', 'PROP_line', 'ROUTE_polygon', 'ROUTE_line', 'LIEUDIT_point', 'INFRA_point', 'INFRA_polygon', 'INFRA_line', 'COM_point', 'COM_line', 'PARCA_polygon_LEGEND']
            import_vectors_from_config(styles_directory, forest_directory, "new_directories", forest_prefix, vector_layers)
            
            zoom_on_layer("Légende")
            replier()
            
            map_themes = [("0_work",
                            ['Unité d analyse', 'Parcelle cadastrale *', 'Limite de propriété', 'ROUTE_polygon', 'ROUTE_line', 'IGN BDORTHO IRC 20cm'],
                            ['Aménagements (UA)', 'Occupation du sol', 'Peuplements (UA)', 'Sous-parcelle forestière', 'Parcelle forestière', 'Limite de parcelle forestière', 'LIEUDIT_point', 'INFRA_point', 'INFRA_polygon', 'INFRA_line', 'COM_point', 'COM_line', 'Légende', 'IGN SCAN 25 TOPO (Metropole) gray', 'IGN SCAN 100 TOPO (Metropole)', 'IGN SCAN 1000 TOPO (Metropole)', 'IGN BDORTHO RGB 20cm', 'IGN Parcellaire Image']),
                          ("1_Vector_plt",
                            ['Peuplements (SSPF)', 'Sous-parcelle forestière', 'Parcelle forestière', 'Limite de parcelle forestière', 'Limite de propriété', 'ROUTE_polygon', 'ROUTE_line', 'LIEUDIT_point', 'INFRA_point', 'INFRA_polygon', 'INFRA_line', 'COM_point', 'COM_line'],
                            ['Aménagements (UA)', 'Occupation du sol', 'Peuplements (UA)', 'Unité d analyse', 'Parcelle cadastrale *', 'Légende', 'IGN SCAN 25 TOPO (Metropole) gray', 'IGN SCAN 100 TOPO (Metropole)', 'IGN SCAN 1000 TOPO (Metropole)', 'IGN BDORTHO IRC 20cm', 'IGN BDORTHO RGB 20cm', 'IGN Parcellaire Image']),
                          ("2_Vector_ame",
                            ['Aménagements (UA)', 'Sous-parcelle forestière', 'Parcelle forestière', 'Limite de parcelle forestière', 'Limite de propriété', 'ROUTE_polygon', 'ROUTE_line', 'LIEUDIT_point', 'INFRA_point', 'INFRA_polygon', 'INFRA_line', 'COM_point', 'COM_line'],
                            ['Occupation du sol', 'Peuplements (UA)', 'Unité d analyse', 'Parcelle cadastrale *', 'Peuplements (SSPF)', 'Légende', 'IGN SCAN 25 TOPO (Metropole) gray', 'IGN SCAN 100 TOPO (Metropole)', 'IGN SCAN 1000 TOPO (Metropole)', 'IGN BDORTHO IRC 20cm', 'IGN BDORTHO RGB 20cm', 'IGN Parcellaire Image']),
                          ("3_Raster_plt",
                            ['Peuplements (SSPF)', 'Sous-parcelle forestière', 'Parcelle forestière', 'Limite de parcelle forestière', 'Limite de propriété', 'ROUTE_polygon', 'ROUTE_line', 'LIEUDIT_point', 'INFRA_point', 'INFRA_polygon', 'INFRA_line', 'COM_point', 'COM_line', 'IGN SCAN 100 TOPO (Metropole)'],
                            ['Aménagements (UA)', 'Occupation du sol', 'Peuplements (UA)', 'Unité d analyse', 'Parcelle cadastrale *', 'Légende', 'IGN SCAN 25 TOPO (Metropole) gray', 'IGN SCAN 1000 TOPO (Metropole)', 'IGN BDORTHO IRC 20cm', 'IGN BDORTHO RGB 20cm', 'IGN Parcellaire Image']),
                          ("4_Raster_ame",
                            ['Aménagements (UA)', 'Sous-parcelle forestière', 'Parcelle forestière', 'Limite de parcelle forestière', 'Limite de propriété', 'ROUTE_polygon', 'ROUTE_line', 'LIEUDIT_point', 'INFRA_point', 'INFRA_polygon', 'INFRA_line', 'COM_point', 'COM_line', 'IGN SCAN 100 TOPO (Metropole)'],
                            ['Occupation du sol', 'Peuplements (UA)', 'Unité d analyse', 'Parcelle cadastrale *', 'Peuplements (SSPF)', 'Légende', 'IGN SCAN 25 TOPO (Metropole) gray', 'IGN SCAN 1000 TOPO (Metropole)', 'IGN BDORTHO IRC 20cm', 'IGN BDORTHO RGB 20cm', 'IGN Parcellaire Image'])]
            for theme in map_themes:
                create_map_theme(*theme)
            
            self.iface.messageBar().pushMessage("QSequoia2", "PEUPLEMENTS généré avec succès", level=Qgis.Success, duration=10)
            
        if map_project == 'GEOLOGIE':
            import_wms_from_config(["GEOL"])
            
            vector_layers = ['GEOL_polygon', 'UA_polygon', 'PF_polygon', 'PF_line', 'PROP_line', 'PARCA_polygon_LEGEND']
            import_vectors_from_config(styles_directory, forest_directory, "new_directories", forest_prefix, vector_layers)
            
            zoom_on_layer("Légende")
            replier()
            
            map_themes = [("0_Geol",
                            ['Géologie', 'Parcelle cadastrale *', 'Parcelle forestière', 'Limite de parcelle forestière', 'Limite de propriété', "BRGM BD Scan-Geol-50"],
                            ['Unité d analyse', 'Légende'])]
            for theme in map_themes:
                create_map_theme(*theme)
            
            self.iface.messageBar().pushMessage("QSequoia2", "GEOLOGIE généré avec succès", level=Qgis.Success, duration=10)
            
        if map_project == 'ENJEUX':
            import_wms_from_config(["Scan25_gray"])
            customize('IGN SCAN 25 TOPO (Metropole) gray')
            
            vector_layers = ['PF_polygon', 'PF_line', 'PROP_line', 'PARCA_polygon_LEGEND']
            import_vectors_from_config(styles_directory, forest_directory, "new_directories", forest_prefix, vector_layers)
            
            zoom_on_layer("Légende")
            replier()
            
            map_themes = [("1_Enjeux",
                            ['Parcelle forestière', 'Limite de parcelle forestière', 'Limite de propriété', 'IGN SCAN 25 TOPO (Metropole) gray'],
                            ['Légende'])]
            for theme in map_themes:
                create_map_theme(*theme)
            
            self.iface.messageBar().pushMessage("QSequoia2", "ENJEUX généré avec succès", level=Qgis.Success, duration=10)
