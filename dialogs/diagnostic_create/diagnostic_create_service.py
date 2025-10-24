from pathlib import Path
import processing

from qgis.core import (
    Qgis,
    QgsProject,
    QgsProcessing,
    QgsFieldConstraints,
    QgsMapLayer,
    QgsSymbol,
    QgsRendererCategory,
    QgsCategorizedSymbolRenderer,
    QgsSimpleLineSymbolLayer,
    QgsSymbolLayer,
    QgsProperty,
    QgsSingleSymbolRenderer,
    QgsSimpleMarkerSymbolLayer
)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import Qt
from qgis.utils import iface

from ...core.layer_factory import LayerFactory
from ...core.layer.manager import LayerManager
from ...utils.config import get_peuplements, get_limites_config, get_limites, get_pictos
from ...utils.layers import load_gpkg, create_relation, load_vectors
from ...utils.utils import fold

class DiagnosticService:
    def __init__(
        self,
        dmin: int,
        dmax: int,
        hmin: int,
        hmax: int,
        essences_layer: dict,
        grid_controller
    ):
        self.iface = iface
        self.project = QgsProject.instance()
        self.root = self.project.layerTreeRoot()
        self.dmin, self.dmax = dmin, dmax
        self.hmin, self.hmax = hmin, hmax
        self.essences_layer = essences_layer
        self.grid_controller = grid_controller

    def run(self):
        """
        Runs the full workflow. 
        Returns the output_dir path (as str) if packaging was done, otherwise None.
        Raises on any error.
        """
        
        print("_create_and_load_gpkg")
        self._create_and_load_gpkg()

        print("_create_relations")
        self._create_relations()

        # PLACETTE
        print("configure PLACETTE layer")
        placette_manager = LayerManager("Placette")
        self._init_placette_form(placette_manager)
        self._configure_placette(placette_manager)
        self._style_placette(placette_manager)
        placette_manager.layer.setCustomProperty("QFieldSync/value_map_button_interface_threshold", 15)
        
        # TRANSECT
        print("configure TRANSECT layer")
        transect_manager = LayerManager("Transect")
        self._init_transect_form(transect_manager)
        self._configure_transect(transect_manager)
        self._style_transect(transect_manager)
        transect_manager.layer.setCustomProperty("QFieldSync/value_map_button_interface_threshold", 99)

        # LIMITE
        print("configure LIMITE layer")
        limite_manager = LayerManager("Limite")
        self._init_limite_form(limite_manager)
        self._configure_limite(limite_manager)
        self._style_limite(limite_manager)

        # PICTO
        print("configure PICTO layer")
        picto_manager = LayerManager("Picto")
        self._init_picto_form(picto_manager)
        self._configure_picto(picto_manager)
        self._style_picto(picto_manager)

        # GHA
        print("configure GHA layer")
        gha_manager = LayerManager("Gha")
        self._init_gha_form(gha_manager)  
        self._configure_gha(gha_manager)  
        gha_manager.layer.setCustomProperty("QFieldSync/value_map_button_interface_threshold", 99)

        # TSE
        print("configure TSE layer")
        tse_manager = LayerManager("Tse")
        self._init_tse_form(tse_manager)  
        self._configure_tse(tse_manager)  
        gha_manager.layer.setCustomProperty("QFieldSync/value_map_button_interface_threshold", 99)

        # VA
        va_manager = LayerManager("Va")
        self._init_va_form(va_manager)  
        self._configure_va(va_manager)  
        va_manager.layer.setCustomProperty("QFieldSync/value_map_button_interface_threshold", 99)

        fold()

        return self.gpkg_path

    def _create_and_load_gpkg(self):

        layers = [
            LayerFactory.create("Placette", "DIAGNOSTIC"),
            LayerFactory.create("Transect", "DIAGNOSTIC"),
            LayerFactory.create("Limite", "DIAGNOSTIC"),
            LayerFactory.create("Picto", "DIAGNOSTIC"),
            LayerFactory.create("Gha", "DIAGNOSTIC"),
            LayerFactory.create("Tse", "DIAGNOSTIC"),
            LayerFactory.create("Va", "DIAGNOSTIC"),
            self.essences_layer,
        ]

        result = processing.run("native:package", {
            'LAYERS':      layers,
            'OUTPUT':      QgsProcessing.TEMPORARY_OUTPUT,
            'OVERWRITE':   True,
            'SAVE_STYLES': False
        })

        self.gpkg_path = result['OUTPUT']
        load_gpkg(self.gpkg_path, group_name="DIAGNOSTIC")

        private_layers = ["Gha", "Tse", "Essences", "Va"]
        for layer_name in private_layers:
            layer = LayerManager(layer_name).layer
            layer.setFlags(layer.flags() | QgsMapLayer.Private | QgsMapLayer.Removable)

        pplmt_layer = ['pf_line', 'pf_polygon', 'sspf_polygon', 'sspf_polygon_plt', 'parca_polygon_occup', 'ua_polygon', 'ua_polygon_plt', 'ua_polygon_ame']
        load_vectors(*pplmt_layer, group_name="SEQUOIA")

        if self.grid_controller.is_valid():
            self.grid_controller.add_grid("VECTEUR")

    def _create_relations(self):
        pairs = [
            ('Placette', 'Gha'),
            ('Placette', 'Tse'),
            ('Placette', 'Va')
        ]
        for parent, child in pairs:
            create_relation(
                parent_name = parent, child_name = child,
                parent_field = 'UUID', child_field = 'UUID',
                relation_id = f'{parent}_{child}',
                relation_name = child
            )
    
    @staticmethod
    def _init_placette_form(placette_manager):

        placette_fb = placette_manager.forms
        placette_fb.init_form()

        # ve: stand for visibility_expression
        forest_plt = "('FRF', 'FIF', 'FRM', 'FIM', 'FRR', 'FIR', 'PEU', 'MFT', 'MRT', 'MMT', 'TSB', 'TSN')"
        va_plt = "('REF', 'PLF', 'REM', 'PLM', 'RER', 'PLR')"

        forest_ve = f"\"PLT_TYPE\" IN {forest_plt}"
        va_ve = f"\"PLT_TYPE\" IN {va_plt}"

        # GENERAL
        general_tab = placette_fb.create_tab("Général")
        group = placette_fb.create_group("", parent = general_tab, columns=2)
        placette_fb.new_add_fields(["COMPTEUR", "PLT_PARCELLE"], parent = group)
        placette_fb.new_add_fields(["PLT_TYPE", "PLT_AME", "PLT_RMQ", "PLT_PHOTO"], parent = general_tab)

        # PEUPLEMENT
        tab_peupl = placette_fb.create_tab("Peuplement")
        placette_fb.new_add_relation("Gha", tab_peupl, visibility_expression=forest_ve)
        placette_fb.new_add_fields(["PLT_RICH", "PLT_STADE", "PLT_DMOY", "PLT_ELAG", "PLT_SANIT", "PLT_CLOISO", "PLT_MECA"], parent = tab_peupl)

        # TAILLIS
        tab_taillis = placette_fb.create_tab("Taillis")
        placette_fb.new_add_relation("Tse", tab_taillis, visibility_expression=forest_ve)
        placette_fb.new_add_fields(["TSE_DENS", "TSE_VOL", "TSE_NATURE"], parent = tab_taillis)

        # PLANT/RÉGÉ
        tab_va = placette_fb.create_tab("Plant/Régé")
        placette_fb.new_add_relation("Va", tab_va, visibility_expression=va_ve)
        placette_fb.new_add_fields(["VA_HT", "VA_TX_TROUEE", "VA_VEG_CON", "VA_TX_DEG", "VA_PROTECT"], parent = tab_va)

        # Apply to layer
        placette_fb.apply()

    @staticmethod
    def _configure_placette(placette_manager):
        placette_f = placette_manager.fields

        # ALIASES
        aliases = [
            ("COMPTEUR", "Placette n°"),
            ("PLT_PARCELLE", "PRF/SPRF"),
            ("PLT_TYPE", "Type de peuplement"),
            ("PLT_AME", "Aménagement"), 
            ("PLT_RMQ", "Remarque"), 
            ("PLT_PHOTO", "Photo"),
            # PEUPLEMENT
            ("PLT_RICH", "Richesse"),
            ("PLT_STADE", "Stade"),
            ("PLT_DMOY", "Diamètre Moyen (cm)"),
            ("PLT_ELAG", "Élagage"), 
            ("PLT_SANIT", "Sanitaire"), 
            ("PLT_CLOISO", "Cloisonnement"), 
            ("PLT_MECA", "Mécanisation"),
            # PLANT/REGE
            ("VA_HT", "Hauteur plantation (m)"),
            ("VA_TX_TROUEE", "Taux trouée (%)"),
            ("VA_VEG_CON", "Végétation concurrente"),
            ("VA_TX_DEG", "Dégâts gibier (%)"),
            ("VA_PROTECT", "Protection"),
            # TAILLIS
            ("TSE_DENS", "Densité"),
            ("TSE_VOL", "Volume (st/ha)"),
            ("TSE_NATURE", "Exploitabilité"),
            ]
        
        for field, alias in aliases:
            placette_f.set_alias(field, alias)

        # region GLOBAL
        # UUID
        # If apply_on_update=True, uuid() resets on each children edit: 
        # - Create parent → UUID=A 
        # - Add first child → FK=A 
        # - Edit another child → UUID becomes B (child’s FK=A breaks under Composition) 
        # - Add second child → FK=B 
        # Only the last child stays linked. Using apply_on_update=False keeps the UUID stable so all children link correctly.
        field_name = "UUID"
        placette_f.set_constraint(field_name, QgsFieldConstraints.ConstraintUnique)
        placette_f.set_default_value(field_name, "uuid()", apply_on_update=False)
        placette_f.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)

        # COMPTEUR
        field_name = "COMPTEUR"
        placette_f.set_read_only(field_name)
        placette_f.set_default_value(field_name, 'count("fid") + 1')

        # PLT_PARCELLE
        placette_f.set_constraint("PLT_PARCELLE", QgsFieldConstraints.ConstraintNotNull)

        # PLT_TYPE
        field_name = "PLT_TYPE"
        peuplements = get_peuplements()
        placette_f.add_value_map(field_name, {'map': [{str(name): str(code)} for code, name in peuplements.items()]})
        placette_f.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)

        # PLT_PHOTO
        placette_f.add_external_resource("PLT_PHOTO")

        # endregion

        # region PEUPLEMENT
        # PLT_RICH
        richesse = {
            'TRI': 'Très riche',
            'RRI': 'Riche',
            'MRI': 'Moy. riche',
            'PPA': 'Pauvre',
            'TPA': 'Ruiné',
            'SIN': 'Sinistré'
        }
        placette_f.add_value_map('PLT_RICH', {'map': [{str(name): str(code)} for code, name in richesse.items()]})

        # PLT_STADE
        stade = {
            'SFO': 'Semis / Fourré',
            'GPE': 'Gaulis / Perchis',
            'JEU': 'Jeune',
            'ADU': 'Adulte',
            'MAT': 'Mature',
            'EXP': 'Exploitable',
            'NEX': 'Non exploitable'
        }
        placette_f.add_value_map('PLT_STADE', {'map': [{str(name): str(code)} for code, name in stade.items()]})

        # PLT_DMOY
        placette_f.add_value_map('PLT_DMOY', {'map': [{str(d): str(d)} for d in range(5, 150 + 1, 10)]})

        # PLT_ELAG
        elagage = {'2m':'2m', '4m': '4m', '6m': '6m'}
        placette_f.add_value_map('PLT_ELAG', {'map': [{str(name): str(code)} for code, name in elagage.items()]})

        # PLT_SANIT
        sanitaire = {
            'AFF_EPARS': 'Affaiblissements épars',
            'AFF_GEN': 'Affaiblissements généralisés',
            'DEP_EPARS': 'Dépérissements épars',
            'DEP_GEN': 'Dépérissements généralisés'
        }
        placette_f.add_value_map('PLT_SANIT', {'map': [{str(name): str(code)} for code, name in sanitaire.items()]})

        # PLT_CLOISO
        cloiso = {
            'Irrégulier': 'Irrégulier',
            '7m': '7m',
            '12m': '12m',
            '15m': '15m',
            '20m': '20m',
            '25m': '25m',
            '30m': '30m',
        }
        placette_f.add_value_map('PLT_CLOISO', {'map': [{str(name): str(code)} for code, name in cloiso.items()]})

        # PLT_MECA
        mecanisable = {
            'M': 'Mécanisable',
            'M_SEMI': 'Semi-mécanisable',
            'M_PARTIE': 'Mécanisable en partie',
            'M_TREUIL': 'Mécanisable - Treuil',
            'NM_PENTE': 'Non mécanisable - Pente',
            'NM_ROCHE': 'Non mécanisable - Roches',
            'NM_HUMIDE': 'Non mécanisable - Humide'
        }
        placette_f.add_value_map('PLT_MECA', {'map': [{str(name): str(code)} for code, name in mecanisable.items()]})
        # endregion

        # region PLANT/REGE
        # VA_HT
        placette_f.add_value_map('VA_HT', {'map': [{str(h): str(h)} for h in [0.5, 1, 1.5, 2, 2.5] + list(range(3, 10 + 1))]})

        # VA_TX_TROUEE
        tx_trouee = {         
            '<10': '<10% (1/10)',
            '10': '10% (1/10)',
            '20': '20% (1/5)',
            '25': '25% (1/4)',
            '33': '33% (1/3)',
            '50': '50% (1/2)',
            '66': '66% (2/3)',
            '>66': '+ de 66% (2/3)',
        }
        placette_f.add_value_map('VA_TX_TROUEE', {'map': [{str(name): str(code)} for code, name in tx_trouee.items()]})

        # VA_VEG_CON
        veg_con = {
            '2': 'Dense / Nettoyage urgent',
            '1': 'Moyenne / Nettoyage à programmer',
            '0': 'Maitrisée / Pas de nettoyage',
        }
        placette_f.add_value_map('VA_VEG_CON', {'map': [{str(name): str(code)} for code, name in veg_con.items()]})

        # VA_TX_DEG
        tx_deg = {         
            '<10': '<10% (1/10)',
            '10': '10% (1/10)',
            '20': '20% (1/5)',
            '25': '25% (1/4)',
            '33': '33% (1/3)',
            '50': '50% (1/2)',
            '66': '66% (2/3)',
            '>66': '+ de 66% (2/3)',
        }
        placette_f.add_value_map('VA_TX_DEG', {'map': [{str(name): str(code)} for code, name in tx_deg.items()]})

        # VA_PROTECT
        protect = {
            'CLOTURE': 'Clôture',
            'INDIV_MECA': 'Individuelle méca',
            'INDIV_CHIMIQUE': 'Individuelle chimique',
        }
        placette_f.add_value_map('VA_PROTECT', {'map': [{str(name): str(code)} for code, name in protect.items()]})
        # endregion

        # region TAILLIS
        # TSE_DENS
        densite = {
            'tres_dense': 'Très dense',
            'dense': 'Dense',
            'moyennement_dense': 'Moyennement dense',
            'peu_dense': 'Peu dense',
            'absent': 'Absent',
        }
        placette_f.add_value_map('TSE_DENS', {'map': [{str(name): str(code)} for code, name in densite.items()]})

        # TSE_VOL
        tse_vol = {
            "25": "25",
            "50": "50",
            "75": "75",
            "100": "100",
            "125": "125",
            "150": "150",
            "200": "200",
            "250": "250",
            "300": "300",
            "350": "350",
            "400": "400",
        }
        placette_f.add_value_map('TSE_VOL', {'map': [{str(name): str(code)} for code, name in tse_vol.items()]})

        # TSE_NATURE
        nature = {
            "BI_BC" : "BI/BC", 
            "BE" : "BE"
        }
        placette_f.add_value_map('TSE_NATURE', {'map': [{str(name): str(code)} for code, name in nature.items()]})
        # endregion
        return None

    @staticmethod
    def _style_placette(placette_manager):
        layer = placette_manager.layer
        s = layer.renderer().symbol()
        s.symbolLayer(0).setSize(3)
        layer.triggerRepaint()

    @staticmethod
    def _init_transect_form(transect_manager):

        transect_fb = transect_manager.forms
        transect_fb.init_form()

        transect_fb.new_add_fields(["TR_PARCELLE"])
        grp_essence = transect_fb.create_group(name="Essence")
        transect_fb.new_add_fields(["TR_TYPE_ESS", "TR_ESS"], grp_essence)

        grp_dendro = transect_fb.create_group(name="Dendrométrie", columns=2)
        transect_fb.new_add_fields(["TR_DIAM", "TR_HAUTEUR"], grp_dendro)

        transect_fb.new_add_fields(["TR_EFFECTIF"])
        
        transect_fb.apply()
    
    def _configure_transect(self, transect_manager):
        transect_f = transect_manager.fields

        # ALIASES
        aliases = [
            ("TR_PARCELLE", "PRF/SPRF"),
            ("TR_TYPE_ESS", "Type Essence"),
            ("TR_ESS", "Essence Transect"),
            ("TR_DIAM", "Diamètre (cm)"),
            ("TR_HAUTEUR", "Hauteur (m)"),
            ("TR_EFFECTIF", "Effectif"),]
        
        for field, alias in aliases:
            transect_f.set_alias(field, alias)

        # UUID
        # If apply_on_update=True, uuid() resets on each children edit: 
        # - Create parent → UUID=A 
        # - Add first child → FK=A 
        # - Edit another child → UUID becomes B (child’s FK=A breaks under Composition) 
        # - Add second child → FK=B 
        # Only the last child stays linked. Using apply_on_update=False keeps the UUID stable so all children link correctly.
        field_name = "UUID"
        transect_f.set_constraint(field_name, QgsFieldConstraints.ConstraintUnique)
        transect_f.set_default_value(field_name, "uuid()", apply_on_update=False)
        transect_f.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)

        # TR_PARCELLE
        field_name = "TR_PARCELLE"
        filtre = f"""
            $id = maximum($id, group_by:="{field_name}")
            AND
            aggregate(
                'Gha',
                'count',
                1,
                filter := "UUID" = attribute(@parent, 'UUID')
            ) > 0
            """
        config = {
            'FilterExpression': filtre,
            'Key': 'PLT_PARCELLE',
            'LayerName': 'Placette',
            'Value': 'PLT_PARCELLE'
        }
        transect_f.add_value_relation(field_name, config)

        # TR_TYPE_ESS
        field_name = "TR_TYPE_ESS"
        types = {f["type"]: f["type"] for f in self.essences_layer.getFeatures()}
        transect_f.add_value_map(field_name, {'map': [{str(name): str(code)} for code, name in types.items()]})

        # TR_ESS
        field_name = "TR_ESS"
        transect_f.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        config = {
            'FilterExpression': f"\"type\" = current_value('TR_TYPE_ESS')",
            'Key': 'fid',
            'LayerName': self.essences_layer.name(),
            'Value': 'essence_variation'
        }
        transect_f.add_value_relation(field_name, config)
        transect_f.set_default_value(field_name, "current_value('TR_TYPE_ESS')")

        # TR_DIAM
        field_name = "TR_DIAM"
        transect_f.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        transect_f.add_value_map(field_name, {'map': [{str(d): str(d)} for d in range(self.dmin, self.dmax + 1, 5)]})
        expression = '"TR_DIAM" != \'\''
        description = "Le champ TR_DIAM ne peut pas être vide."
        transect_f.set_constraint_expression(field_name, expression, description, QgsFieldConstraints.ConstraintStrengthHard)

        # TR_HAUTEUR
        field_name = "TR_HAUTEUR"
        transect_f.add_value_map(field_name, {'map': [{str(h): str(h)} for h in range(self.hmin, self.hmax + 1)]})

        # TR_EFFECTIF
        field_name = "TR_EFFECTIF"
        transect_f.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        transect_f.add_range(field_name, {'AllowNull': False, 'Max': 1000, 'Min': 0, 'Precision': 0, 'Step': 1})
        transect_f.set_default_value(field_name, '1', False)

    @staticmethod
    def _style_transect(transect_manager):
        layer = transect_manager.layer
        s = layer.renderer().symbol()
        s.symbolLayer(0).setSize(2)
        layer.triggerRepaint()

    @staticmethod
    def _init_gha_form(gha_manager):
        gha_manager.forms.init_form()
        gha_manager.forms.new_add_fields(["GHA_ESS", "GHA_G"])

    def _configure_gha(self, gha_manager):
        gha_f = gha_manager.fields

        # ALIASES
        aliases = [
            ("GHA_ESS", "Essence Gha"),
            ("GHA_G", "Surface terrière")
        ]
        
        for field, alias in aliases:
            gha_f.set_alias(field, alias)
        
        # DISPLAY EXPRESSION
        display_expression = """
            WITH_VARIABLE(
                'ess',
                get_feature('Essences', 'fid', "GHA_ESS"),
                concat(
                    attribute(@ess, 'essence_variation'),
                    ' : ',
                    "GHA_G",
                    ' m²/ha '
                )
            )
            """
        gha_manager.set_display_expression(display_expression)

        # GHA_ESS
        field_name = "GHA_ESS"
        gha_f.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        config = {
            'FilterExpression': '"variation" IS NULL',
            'Key': 'fid',
            'LayerName': self.essences_layer.name(),
            'Value': 'essence_variation'
        }
        gha_f.add_value_relation(field_name, config)

        # GHA_G
        field_name = "GHA_G"
        gha_f.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        gha_f.set_constraint_expression(field_name, f'"{field_name}" > 0', "La surface terrière doit être supérieur à 0", strength=QgsFieldConstraints.ConstraintStrengthHard)
        gha_f.set_default_value(field_name, '1', False)
        gha_f.add_range(field_name, {'AllowNull': False, 'Max': 100, 'Min': 0, 'Precision': 0, 'Step': 1})

    @staticmethod
    def _init_va_form(va_manager):
        va_manager.forms.init_form()
        va_manager.forms.new_add_fields(["VA_ESS", "VA_TX_HA", "VA_CUMUL_TX_VA"])

    def _configure_va(self, va_manager):
        va_f = va_manager.fields

        # ALIASES
        aliases = [
            ("VA_ESS", "Essence Plant/Régé"),
            ("VA_TX_HA", "Proportion [1 ess => 100%]"),
            ("VA_CUMUL_TX_VA", "Cumul des recouvrements"),
        ]
        
        for field, alias in aliases:
            va_f.set_alias(field, alias)
        
        # DISPLAY EXPRESSION
        display_expression = """
            WITH_VARIABLE(
                'ess',
                get_feature('Essences', 'fid', "VA_ESS"),
                concat(
                    attribute(@ess, 'essence_variation'),
                    ' : ',
                    "VA_TX_HA",
                    ' %'
                )
            )
            """
        va_manager.set_display_expression(display_expression)

        # VA_ESS
        field_name = "VA_ESS"
        va_f.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        config = {
            'FilterExpression': '"variation" IS NULL',
            'Key': 'fid',
            'LayerName': self.essences_layer.name(),
            'Value': 'essence_variation'
        }
        va_f.add_value_relation(field_name, config)

        # VA_TX_HA
        field_name = "VA_TX_HA"
        va_f.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        expression = '"VA_CUMUL_TX_VA" + "VA_TX_HA" = 100'
        description = 'La somme de VA_TX_HA et de VA_CUMUL_TX_VA doit être égale à 100.'
        va_f.set_constraint_expression(field_name, expression, description)
        va_f.add_range(field_name, {'AllowNull': False, 'Max': 100, 'Min': 0, 'Precision': 0, 'Step': 10})

        # CUMUL_TX_VA
        field_name = "VA_CUMUL_TX_VA"
        default_value = """aggregate(layer:='Va', aggregate:='sum', expression:="VA_TX_HA", filter:="UUID" = attribute(@parent, 'UUID'))"""
        va_f.set_default_value(field_name, default_value)
        va_f.set_read_only(field_name)

    @staticmethod
    def _init_tse_form(tse_manager):
        tse_manager.forms.init_form()
        tse_manager.forms.new_add_fields(["TSE_ESS", "TSE_DIM"])

    def _configure_tse(self, tse_manager):
        tse_f = tse_manager.fields

        # ALIASES
        aliases = [
            ("TSE_ESS", "Essence Taillis"),
            ("TSE_DIM", "Dimension"),
        ]
        
        for field, alias in aliases:
            tse_f.set_alias(field, alias)

        # DISPLAY EXPRESSION
        display_expression = """
            WITH_VARIABLE(
                'ess',
                get_feature('Essences', 'fid', "TSE_ESS"),
                concat(attribute(@ess, 'essence_variation'), ' : ', "TSE_DIM")
            )
            """
        tse_manager.set_display_expression(display_expression)

        # TSE_ESS
        field_name = "TSE_ESS"
        tse_f.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        config = {
            'FilterExpression': '"variation" IS NULL',
            'Key': 'fid',
            'LayerName': self.essences_layer.name(),
            'Value': 'essence_variation'
        }
        tse_f.add_value_relation(field_name, config)

        # TSE_DIM
        tse_dim = {
                '<5': '<5 cm',
                '5-15': '5-15 cm',
                '10-30': '10-30 cm',
                '25-45': '25-45 cm',
                '>40': '>40 cm'
            }
        tse_f.add_value_map('TSE_DIM', {'map': [{str(name): str(code)} for code, name in tse_dim.items()]})

    @staticmethod
    def _init_limite_form(limite_manager):
        limite_manager.forms.init_form()
        limite_manager.forms.new_add_fields(["LIMITE_TYPE", "LIMITE_RMQ", "LIMITE_PHOTO"])

    @staticmethod
    def _configure_limite(limite_manager):
        limite_f = limite_manager.fields

        # ALIASES
        aliases = [
            ("LIMITE_TYPE", "Type"),
            ("LIMITE_RMQ", "Remarque"),
            ("LIMITE_PHOTO", "Photo"),
        ]
        
        for field, alias in aliases:
            limite_f.set_alias(field, alias)

        # LIMITE_TYPE
        limites = get_limites()
        limite_f.add_value_map('LIMITE_TYPE', {'map': [{str(name): str(code)} for code, name in limites.items()]})

        # LIMITE_PHOTO
        limite_f.add_external_resource("LIMITE_PHOTO")

    @staticmethod
    def _style_limite(limite_manager):
        field = 'LIMITE_TYPE'
        layer = limite_manager.layer
        cfg = get_limites_config()  # YAML → dict

        style_map = {
            "solid": Qt.SolidLine,
            "dash": Qt.DashLine,
            "dot": Qt.DotLine,
            "dashdot": Qt.DashDotLine,
            "dashdotdot": Qt.DashDotDotLine,
        }

        categories = []
        for code, props in cfg.items():
            color = QColor(props.get("color", "black"))
            width = float(props.get("width", 0.8))
            line_type = props.get("style", "solid").lower()
            label = props.get("label", code)

            line_layer = QgsSimpleLineSymbolLayer()
            line_layer.setColor(color)
            line_layer.setWidth(width)
            line_layer.setPenStyle(style_map.get(line_type, Qt.SolidLine))

            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            symbol.deleteSymbolLayer(0)
            symbol.appendSymbolLayer(line_layer)

            categories.append(QgsRendererCategory(code, symbol, label))

        renderer = QgsCategorizedSymbolRenderer(field, categories)
        layer.setRenderer(renderer)
        layer.triggerRepaint()

    @staticmethod
    def _init_picto_form(picto_manager):
        picto_f = picto_manager.forms
        picto_f.init_form()
        picto_f.new_add_fields(["PICTO_TYPE", "PICTO_RMQ", "PICTO_PHOTO"])
        grp_shape = picto_f.create_group(name="Symbologie", columns=2)
        picto_f.new_add_fields(["PICTO_COLOR", "PICTO_SHAPE"], grp_shape)

    @staticmethod
    def _configure_picto(picto_manager):
        picto_f = picto_manager.fields

        # ALIASES
        aliases = [
            ("PICTO_TYPE", "Type"),
            ("PICTO_RMQ", "Remarque"),
            ("PICTO_PHOTO", "Photo"),
            ("PICTO_COLOR", "Couleur"),
            ("PICTO_SHAPE", "Forme"),
        ]
        
        for field, alias in aliases:
            picto_f.set_alias(field, alias)

        # PICTO_TYPE
        pictos = get_pictos()
        picto_f.add_value_map('PICTO_TYPE', {'map': [{str(name): str(code)} for code, name in pictos.items()]})

        # PICTO_PHOTO
        # Whould be available next release !
        # picto_f.add_color_picker("PICTO_COLOR")
        # picto_f.set_default_value("PICTO_COLOR", "'#191970'")
        color_map = {
            "Rouge": "#e41a1c",
            "Bleu": "#377eb8",
            "Vert": "#4daf4a",
            "Violet": "#984ea3",
            "Orange": "#ff7f00",
        }

        picto_f.add_value_map(
            "PICTO_COLOR",
            {"map": [{label: hexval} for label, hexval in color_map.items()]}
        )
        picto_f.set_default_value("PICTO_COLOR", "'#e41a1c'")

        # PICTO_SHAPE
        shape_map = {
            "Cercle": "circle",
            "Carré": "square",
            "Triangle": "triangle",
            "Croix": "cross",
            "X": "cross2",
            "Losange": "diamond",
            "Étoile": "star",
            "Coeur": "heart",
        }

        # Store enum values as integers (Qgis.MarkerShape is an IntEnum)
        picto_f.add_value_map("PICTO_SHAPE", {"map": [{label: shape} for label, shape in shape_map.items()]})
        picto_f.set_default_value("PICTO_SHAPE", "'triangle'")

    @staticmethod
    def _style_picto(picto_manager):
        layer = picto_manager.layer
        
        sym_layer = QgsSimpleMarkerSymbolLayer()
        sym_layer.setDataDefinedProperty(QgsSymbolLayer.PropertyFillColor, QgsProperty.fromExpression('"PICTO_COLOR"'))
        sym_layer.setDataDefinedProperty(QgsSymbolLayer.PropertyName, QgsProperty.fromExpression('"PICTO_SHAPE"'))

        # Wrap in a symbol (container)
        symbol = QgsSymbol.defaultSymbol(layer.geometryType())
        symbol.deleteSymbolLayer(0)
        symbol.appendSymbolLayer(sym_layer)

        # Apply to layer
        layer.setRenderer(QgsSingleSymbolRenderer(symbol))
        layer.triggerRepaint()


