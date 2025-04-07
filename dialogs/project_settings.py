from PyQt5.QtWidgets import *
from .project_settings_dialog import Ui_ProjectSettingsDialog
from qgis.core import *
from qgis.PyQt.QtCore import *
import os

# Import from utils folder
from ..utils.variable_utils import *
from ..utils.layer_utils import *

class ProjectSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.ui = Ui_ProjectSettingsDialog()
        self.ui.setupUi(self)
        
        # Liste des projets possibles
        self.projects = ["SITUATION", "ASSEMBLAGE", "PEUPLEMENTS", "GEOLOGIE", "ENJEUX"]
        self.ui.comboBox_projects.addItems(self.projects)
        
        # Charger les paramètres existants
        self.load_settings()

        # Connecter les boutons
        self.ui.buttonBox.accepted.connect(self.save_settings)
        self.ui.pushButton.clicked.connect(self.select_directory)
        self.ui.checkBox_domaine.toggled.connect(self.refresh_cartouche)
        self.ui.checkBox_massif.toggled.connect(self.refresh_cartouche)
        self.ui.checkBox_foret.toggled.connect(self.refresh_cartouche)
        self.ui.checkBox_bois.toggled.connect(self.refresh_cartouche)
        self.ui.pushButton_refresh.clicked.connect(self.get_cartouche)

    def load_settings(self):
        # Directory
        directory = get_project_variable("forest_directory")
        if directory:
            self.ui.lineEdit_directory.setText(directory)

        # Prefix
        prefix = get_project_variable("forest_prefix")
        if prefix:
            self.ui.lineEdit_prefixe.setText(prefix)
        
        # Name
        temp_name  = get_project_variable("forest_temp_name")
        if temp_name:
            self.ui.lineEdit_name.setText(temp_name)
        
        # City
        city = get_project_variable("forest_city")
        if city:
            self.ui.lineEdit_city.setText(city)
            
        # owner
        owner = get_project_variable("forest_owner")
        if owner:
            self.ui.lineEdit_owner.setText(owner)
            
        # surface
        surface = get_project_variable("forest_surface")
        if surface:
            self.ui.doubleSpinBox.setValue(surface)

        # Charger le projet de carte sélectionné
        map_project = get_project_variable("forest_map_project")
        if map_project:
            self.ui.comboBox_projects.setCurrentText(map_project)

    def save_settings(self):
      
        # Récupère les paramètres
        directory = self.ui.lineEdit_directory.text()
        prefix = self.ui.lineEdit_prefixe.text()
        name =  self.ui.lineEdit_name.text()
        city =  self.ui.lineEdit_city.text()
        owner =  self.ui.lineEdit_owner.text()
        surface = self.ui.doubleSpinBox.value()
        formated_surface = get_formated_surface(surface*10000)
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
        UserPath = os.path.expanduser("~")
        StartPath = os.path.join(UserPath, "Racines", "Cartographie - Documents", "2_FORETS")
        dir_path = QFileDialog.getExistingDirectory(self, "Sélectionner le répertoire de travail", StartPath)
        
        if dir_path:
            # Directory
            self.ui.lineEdit_directory.setText(dir_path)
            
            # Prefix
            prefix = get_prefix_from_directory(dir_path)
            self.ui.lineEdit_prefixe.setText(prefix)
            
            self.get_cartouche()
            
    
    def get_cartouche(self):
        directory = self.ui.lineEdit_directory.text()
        prefix = self.ui.lineEdit_prefixe.text()
        
        if directory and prefix:
            # Nom
            name = prefix.title()
            self.ui.lineEdit_name.setText(name)
            set_project_variable("forest_temp_name", name)
                
            # Commune
            parca_path = get_vector_from_config(directory, "new_directories", prefix, "PARCA_polygon")
            if parca_path:
                city = get_grouped_values_from_shapefile(parca_path, "COM_NOM", "DEP_CODE", "SURF_CA")
                self.ui.lineEdit_city.setText(city)
                
            # Surface
            ua_path = get_vector_from_config(directory, "new_directories", prefix, "UA_polygon")
            if os.path.exists(ua_path):
                surface = sum_surface_from_shapefile(ua_path, "SURF_COR", "OCCUP_SOL", "BOISEE")
                self.ui.doubleSpinBox.setValue(surface)
            elif os.path.exists(parca_path):
                surface = sum_surface_from_shapefile(parca_path, "SURF_CA", None, None)
                self.ui.doubleSpinBox.setValue(surface)
                
            # Proprietaire
            owner = get_grouped_values_from_shapefile(parca_path, "PROP", None, "SURF_CA")
            self.ui.lineEdit_owner.setText(owner)
        
            
    def refresh_cartouche(self):
        name= get_project_variable("forest_temp_name")
        if not name:
            name = get_project_variable("forest_name")
        
        full_name = ""
        
        if self.ui.checkBox_domaine.isChecked():
            full_name = "Domaine de " + name
        elif  self.ui.checkBox_massif.isChecked():
            full_name = "Massif de " + name
        elif  self.ui.checkBox_foret.isChecked():
            full_name = "Forêt de " + name
        elif  self.ui.checkBox_bois.isChecked():
            full_name = "Bois de " + name
            
        if not full_name:
            full_name = name
        
        self.ui.lineEdit_name.setText(full_name)
      
    def save_current_project(self, map_project):
        if self.ui.checkBox_saved.isChecked():
            forest_directory = get_project_variable("forest_directory")
            project = QgsProject.instance()
            save_path = os.path.join(forest_directory, "SIG", "0_OUTPUT", map_project + ".qgz")
            project.write(save_path)
            project.write()
            
    def create_map_project(self, map_project):
        clear_qgis_project()
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
