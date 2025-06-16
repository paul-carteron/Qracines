from pathlib import Path
import processing

from qgis.core import (
    QgsProject,
    QgsProcessing,
    QgsFieldConstraints,
    QgsFeatureRequest,
    QgsExpression,
    QgsPalLayerSettings,
    QgsTextFormat,
    QgsVectorLayerSimpleLabeling
)

from qgis.utils import iface

from PyQt5.QtCore import QVariant
from PyQt5.QtGui import QFont

from ..core.layer_factory import LayerFactory
from ..core.db.manager import DatabaseManager
from ..core.layer.manager import LayerManager
from ..utils.path_manager import get_peuplements
from ..utils.layer_utils import add_layers_from_gpkg, create_relation
from ..utils.qfield_utils import package_for_qfield
from ..utils.variable_utils import get_project_variable


class ExpertiseService:

    def __init__(
        self,
        output_dir: Path,
        package_for_qfield: bool,
        codes: list,
        codes_taillis: list,
        dmin: int,
        dmax: int,
        hmin: int,
        hmax: int,
        essences_layer: dict
    ):
        self.iface = iface
        self.project = QgsProject.instance()
        self.root = self.project.layerTreeRoot()
        self.output_dir = output_dir
        self.package_for_qfield = package_for_qfield
        self.codes = codes
        self.codes_taillis = codes_taillis
        self.dmin, self.dmax = dmin, dmax
        self.hmin, self.hmax = hmin, hmax
        self.essences_layer = essences_layer

    def run_full_diagnostic(self):
        """
        Runs the full workflow. 
        Returns the output_dir path (as str) if packaging was done, otherwise None.
        Raises on any error.
        """
        self._create_and_load_gpkg()
        self._create_relations()
        essences_manager = LayerManager("essences")

        # PLACETTE
        placette_manager = LayerManager("placette")
        self._init_placette_form(placette_manager)
        self._configure_placette(placette_manager)
        placette_manager.layer.setCustomProperty("QFieldSync/value_map_button_interface_threshold", 13)

        # TRANSECT
        transect_manager = LayerManager("transect")
        self._init_transect_form(transect_manager)
        self._configure_transect(transect_manager, self.dmin, self.dmax, self.hmin, self.hmax)
        self._configure_essence_field(transect_manager, "TR_ESSENCE_ID", "TR_ESSENCE_SECONDAIRE_ID", essences_manager, self.codes, with_variation = True)
        transect_manager.layer.setCustomProperty("QFieldSync/value_map_button_interface_threshold", 99)

        # GHA
        gha_manager = LayerManager("gha")
        self._init_gha_form(gha_manager)  
        self._configure_gha(gha_manager)  
        self._configure_essence_field(gha_manager, "GHA_ESSENCE_ID", "GHA_ESSENCE_SECONDAIRE_ID", essences_manager, self.codes, with_variation = False)
        gha_manager.layer.setCustomProperty("QFieldSync/value_map_button_interface_threshold", 99)

        # TAILLIS
        tse_manager = LayerManager("tse")
        self._init_tse_form(tse_manager)  
        self._configure_tse(tse_manager)  
        self._configure_essence_field(tse_manager, "TSE_ESSENCE_ID", "TSE_ESSENCE_SECONDAIRE_ID", essences_manager, self.codes_taillis, with_variation = False, selected_field = "selected_taillis")
        tse_manager.layer.setCustomProperty("QFieldSync/value_map_button_interface_threshold", 99)

        # VALEUR AVENIR
        va_manager = LayerManager("va")
        self._init_va_form(va_manager)  
        self._configure_va(va_manager)  
        self._configure_essence_field(va_manager, "VA_ESSENCE_ID", "VA_ESSENCE_SECONDAIRE_ID", essences_manager, self.codes, with_variation = False)
        va_manager.layer.setCustomProperty("QFieldSync/value_map_button_interface_threshold", 99)

        # REGENERATION
        reg_manager = LayerManager("reg")
        self._init_reg_form(reg_manager)  
        self._configure_reg(reg_manager)  
        self._configure_essence_field(reg_manager, "REG_ESSENCE_ID", "REG_ESSENCE_SECONDAIRE_ID", essences_manager, self.codes, with_variation = False)
        reg_manager.layer.setCustomProperty("QFieldSync/value_map_button_interface_threshold", 99)

        # Run packaging if needed
        if self.package_for_qfield:
            self._package_for_qfield()
            # signal back that packaging happened
            return str(self.output_dir)
        return None

    def _create_and_load_gpkg(self):

        layers = [
            LayerFactory.create("placette", "EXPERTISE"),
            LayerFactory.create("transect", "EXPERTISE"),
            LayerFactory.create("gha", "EXPERTISE"),
            LayerFactory.create("tse", "EXPERTISE"),
            LayerFactory.create("reg", "EXPERTISE"),
            LayerFactory.create("va", "EXPERTISE"),
            self.essences_layer
        ]

        result = processing.run("native:package", {
            'LAYERS':      layers,
            'OUTPUT':      QgsProcessing.TEMPORARY_OUTPUT,
            'OVERWRITE':   True,
            'SAVE_STYLES': False
        })

        self.gpkg_path = result['OUTPUT']

        # 5) load it back into the project
        add_layers_from_gpkg(self.gpkg_path)

    def _create_relations(self):
        pairs = [
            ('placette', 'gha'),
            ('placette', 'tse'),
            ('placette', 'reg'),
            ('placette', 'va')
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
        placette_manager.forms.init_drag_and_drop_form()
        placette_manager.forms.add_fields_to_tab("COMPTEUR")
        placette_manager.forms.add_fields_to_tab("PLTM_PARCELLE", "PLTM_STRATE", tab_name="Localisation", columns=2)
        placette_manager.forms.add_fields_to_tab("PLTM_TYPE")

        # ve: stand for visibility_expression
        gha_ve = """left("PLTM_TYPE",2)='FR' OR left("PLTM_TYPE",2)='FI' OR left("PLTM_TYPE",2)='MF' OR left("PLTM_TYPE",2)='PE'"""
        tse_ve = """"PLTM_TYPE"<>''"""
        reg_ve = """"PLTM_TYPE"<>''"""
        va_ve = """left("PLTM_TYPE",2)='FR' OR left("PLTM_TYPE",2)='FI' OR left("PLTM_TYPE",2)='PE'"""

        placette_manager.forms.add_relation_to_tab("gha", tab_name="Surface terrière", visibility_expression = gha_ve)
        placette_manager.forms.add_fields_to_tab("TSE_STERE_HA", tab_name="Taillis", visibility_expression = reg_ve)
        placette_manager.forms.add_relation_to_tab("tse", tab_name="Taillis", visibility_expression = tse_ve)
        placette_manager.forms.add_fields_to_tab("VA_TX_TROUEE", tab_name="Valeur d'avenir", visibility_expression = reg_ve)
        placette_manager.forms.add_relation_to_tab("va", tab_name="Valeur d'avenir")
        placette_manager.forms.add_relation_to_tab("reg", tab_name="Régénération", visibility_expression = va_ve)
    
    @staticmethod
    def _configure_placette(placette_manager):
        # ALIASES
        aliases = [
            ("COMPTEUR", "Placette"),
            ("PLTM_PARCELLE", "Parcelle"),
            ("PLTM_STRATE", "Strate"),
            ("PLTM_TYPE", "Type de peuplement"),
            ("VA_TX_TROUEE", "Taux trouée [%]"),
            ("TSE_STERE_HA", "Taillis [st/ha]")]
        
        for field, alias in aliases:
            placette_manager.fields.set_alias(field, alias)

        # UUID
        # If apply_on_update=True, uuid() resets on each children edit: 
        # - Create parent → UUID=A 
        # - Add first child → FK=A 
        # - Edit another child → UUID becomes B (child’s FK=A breaks under Composition) 
        # - Add second child → FK=B 
        # Only the last child stays linked. Using apply_on_update=False keeps the UUID stable so all children link correctly.
        field_name = "UUID"
        placette_manager.fields.set_constraint(field_name, QgsFieldConstraints.ConstraintUnique)
        placette_manager.fields.set_default_value(field_name, "uuid()", apply_on_update=False)
        placette_manager.fields.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)

        # COMPTEUR
        field_name = "COMPTEUR"
        placette_manager.fields.set_read_only(field_name)
        placette_manager.fields.set_default_value(field_name, 'count("fid") + 1')

        # PLTM_PARCELLE & PLTM_STRATE
        expression = '"PLTM_PARCELLE" is not NULL OR "PLTM_STRATE" is not NULL'
        description = "Ajouter une parcelle ou une strate si l'inventaire n'utilise pas de carto"
        placette_manager.fields.set_constraint_expression("PLTM_PARCELLE", expression, description)
        placette_manager.fields.set_constraint_expression("PLTM_STRATE", expression, description)

        # PLTM_TYPE
        peuplements = get_peuplements()
        placette_manager.fields.add_value_map('PLTM_TYPE', {'map': [{str(name): str(code)} for code, name in peuplements.items()]})

        # VA_TX_TROUEE
        placette_manager.fields.add_range("VA_TX_TROUEE", {'AllowNull': True, 'Max': 100, 'Min': 0, 'Precision': 0, 'Step': 10})

        # TSE_STERE_HA
        stere_ha = [*range(0, 200, 25), *range(200, 400, 50)]
        placette_manager.fields.add_value_map("TSE_STERE_HA", {'map': [{str(value): str(value)} for value in stere_ha]})

        return None

    @staticmethod
    def _init_transect_form(transect_manager):
        transect_manager.forms.init_drag_and_drop_form()
        transect_manager.forms.add_fields_to_tab("TR_PARCELLE", "TR_STRATE", tab_name="Localisation", columns=2)
        fields = ["TR_ESSENCE_ID", "TR_ESSENCE_SECONDAIRE_ID", "TR_DIAMETRE", "TR_EFFECTIF", "TR_HAUTEUR"]
        transect_manager.forms.add_fields_to_tab(*fields, tab_name="Dendrométrie")
    
    @staticmethod
    def _configure_transect(transect_manager, dmin, dmax, hmin, hmax):
        # ALIASES
        aliases = [
            ("TR_PARCELLE", "Parcelle"),
            ("TR_STRATE", "Strate"),
            ("TR_ESSENCE_ID", "Essence"),
            ("TR_ESSENCE_SECONDAIRE_ID", "Essence secondaire"),
            ("TR_DIAMETRE", "Diamètre [cm]"),
            ("TR_EFFECTIF", "Effectif"),
            ("TR_HAUTEUR", "Hauteur [m]"),]
        
        for field, alias in aliases:
            transect_manager.fields.set_alias(field, alias)

        # FID
        transect_manager.fields.set_default_value("fid", 'if (maximum("fid") is NULL, 1, maximum("fid") + 1)')

        # UUID
        field_name = "UUID"
        transect_manager.fields.set_constraint(field_name, QgsFieldConstraints.ConstraintUnique)
        transect_manager.fields.set_default_value(field_name, "uuid()")
        transect_manager.fields.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)

        # TR_PARCELLE & TR_STRATE
        expression = '"TR_PARCELLE" is not NULL OR "TR_STRATE" is not NULL'
        description = "Ajouter une parcelle ou une strate si l'inventaire n'utilise pas de carto"
        transect_manager.fields.set_constraint_expression("TR_PARCELLE", expression, description)
        transect_manager.fields.set_constraint_expression("TR_STRATE", expression, description)

        # TR_DIAMETRE
        field_name = "TR_DIAMETRE"
        transect_manager.fields.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        transect_manager.fields.add_value_map(field_name, {'map': [{str(d): str(d)} for d in range(dmin, dmax + 1, 5)]})
        expression = '"TR_DIAMETRE" != \'\''
        description = "Le champ TR_DIAMETRE ne peut pas être vide."
        transect_manager.fields.set_constraint_expression(field_name, expression, description ,QgsFieldConstraints.ConstraintStrengthHard)

        # TR_EFFECTIF
        field_name = "TR_EFFECTIF"
        transect_manager.fields.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        transect_manager.fields.add_range(field_name, {'AllowNull': False, 'Max': 1000, 'Min': 0, 'Precision': 0, 'Step': 1})
        transect_manager.fields.set_default_value(field_name, '1', False)

        # TR_HAUTEUR
        field_name = "TR_HAUTEUR"
        transect_manager.fields.add_value_map(field_name, {'map': [{str(h): str(h)} for h in range(hmin, hmax + 1)]})

        return None
    
    @staticmethod
    def _init_gha_form(gha_manager):
        gha_manager.forms.init_drag_and_drop_form()
        gha_manager.forms.add_fields_to_tab("GHA_ESSENCE_ID", "GHA_ESSENCE_SECONDAIRE_ID", "GHA_G")
    
    @staticmethod
    def _configure_gha(gha_manager):
        # ALIASES
        aliases = [
            ("GHA_ESSENCE_ID", "Essence"),
            ("GHA_ESSENCE_SECONDAIRE_ID", "Essence secondaire"),
            ("GHA_G", "Surface terrière")
        ]
        
        for field, alias in aliases:
            gha_manager.fields.set_alias(field, alias)
        
        # DISPLAY EXPRESSION
        display_expression = """
            WITH_VARIABLE(
                'ess',
                get_feature(
                    'essences',
                    'fid',
                    coalesce(NULLIF("GHA_ESSENCE_ID", ''), "ghA_ESSENCE_SECONDAIRE_ID")
                ),
                concat(attribute(@ess, 'essence_variation'),
                ' : ',
                "GHA_G",
                ' m²/ha ')
            )
            """
        gha_manager.set_display_expression(display_expression)

        # GHA_G
        field_name = "GHA_G"
        gha_manager.fields.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        gha_manager.fields.set_constraint_expression(field_name, f'"{field_name}" > 0', "La surface terrière doit être supérieur à 0", strength=QgsFieldConstraints.ConstraintStrengthHard)
        gha_manager.fields.add_range(field_name, {'AllowNull': False, 'Max': 100, 'Min': 0, 'Precision': 0, 'Step': 1})

    @staticmethod
    def _init_tse_form(tse_manager):
        tse_manager.forms.init_drag_and_drop_form()
        tse_manager.forms.add_fields_to_tab("TSE_ESSENCE_ID", "TSE_ESSENCE_SECONDAIRE_ID")
    
    @staticmethod
    def _configure_tse(tse_manager):
        # ALIASES
        aliases = [
            ("TSE_ESSENCE_ID", "Essence"),
            ("TSE_ESSENCE_SECONDAIRE_ID", "Essence secondaire")
        ]
        
        for field, alias in aliases:
            tse_manager.fields.set_alias(field, alias)
        
        # DISPLAY EXPRESSION
        display_expression = """
            WITH_VARIABLE(
                'ess',
                get_feature(
                    'essences',
                    'fid',
                    coalesce(NULLIF("TSE_ESSENCE_ID", ''), "TSE_ESSENCE_SECONDAIRE_ID")
                ),
                attribute(@ess, 'essence_variation')
            )
            """
        tse_manager.set_display_expression(display_expression)

    @staticmethod
    def _init_va_form(va_manager):
        va_manager.forms.init_drag_and_drop_form()
        va_manager.forms.add_fields_to_tab("VA_ESSENCE_ID", "VA_ESSENCE_SECONDAIRE_ID", "VA_AGE_APP", "VA_TX_HA", "CUMUL_TX_VA")
    
    @staticmethod
    def _configure_va(va_manager):
        # ALIASES
        aliases = [
            ("VA_ESSENCE_ID", "Essence"),
            ("VA_ESSENCE_SECONDAIRE_ID", "Essence secondaire"),
            ("VA_AGE_APP", "Age Apparent"),
            ("VA_TX_HA", "Recouvrement [%]"),
            ("CUMUL_TX_VA", "Cumul des recouvrements"),
        ]
        
        for field, alias in aliases:
            va_manager.fields.set_alias(field, alias)
        
        # DISPLAY EXPRESSION
        display_expression = """
            WITH_VARIABLE(
                'ess',
                get_feature(
                    'essences',
                    'fid',
                    coalesce(NULLIF("VA_ESSENCE_ID", ''), "VA_ESSENCE_SECONDAIRE_ID")
                ),
                concat(
                    attribute(@ess, 'essence_variation'),
                    ' : ',
                    "VA_TX_HA",
                    ' %'
                )
            )
            """
        va_manager.set_display_expression(display_expression)

        # VA_AGE_APP
        field_name = "VA_AGE_APP"
        va_manager.fields.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        va_manager.fields.set_constraint_expression(field_name, f'"{field_name}" > 0', "L'âge doit être supérieur à 0", strength=QgsFieldConstraints.ConstraintStrengthHard)
        va_manager.fields.add_range(field_name, {'AllowNull': False, 'Max': 300, 'Min': 0, 'Precision': 0, 'Step': 1})

        # VA_TX_HA
        field_name = "VA_TX_HA"
        va_manager.fields.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        expression = '"CUMUL_TX_VA" + "VA_TX_HA" = 100'
        description = 'La somme de VA_TX_HA et de CUMUL_TX_VA doit être égale à 100.'
        va_manager.fields.set_constraint_expression(field_name, expression, description)
        va_manager.fields.add_range(field_name, {'AllowNull': False, 'Max': 100, 'Min': 0, 'Precision': 0, 'Step': 10})

        # CUMUL_TX_VA
        field_name = "CUMUL_TX_VA"
        default_value = """aggregate(layer:='va', aggregate:='sum', expression:="VA_TX_HA", filter:="UUID" = attribute(@parent, 'UUID'))"""
        va_manager.fields.set_default_value(field_name, default_value)

    @staticmethod
    def _init_reg_form(reg_manager):
        reg_manager.forms.init_drag_and_drop_form()
        reg_manager.forms.add_fields_to_tab("REG_ESSENCE_ID", "REG_ESSENCE_SECONDAIRE_ID", "REG_STADE", "REG_ETAT")
    
    @staticmethod
    def _configure_reg(reg_manager):
        # ALIASES
        aliases = [
            ("REG_ESSENCE_ID", "Essence"),
            ("REG_ESSENCE_SECONDAIRE_ID", "Essence secondaire"),
            ("REG_STADE", "Stade"),
            ("REG_ETAT", "Etat"),
        ]
        
        for field, alias in aliases:
            reg_manager.fields.set_alias(field, alias)

        # DISPLAY EXPRESSION
        display_expression = """
            WITH_VARIABLE(
                'ess',
                get_feature(
                    'essences',
                    'fid',
                    coalesce(NULLIF("REG_ESSENCE_ID", ''), "REG_ESSENCE_SECONDAIRE_ID")
                ),
                concat(
                    attribute(@ess, 'essence_variation'),
                    ' : ',
                    "REG_STADE",
                    ' - '
                    "REG_ETAT"
                )
            )
            """
        reg_manager.set_display_expression(display_expression)

        # REG_STADE
        stades = {
            "semis_inf_05": "Semis <0.5m",
            "semis_05_1": "Semis 0.5-1m",
            "fourre_1_3": "Fourré 1-3m",
            "semis_3_5": "Gaulis 3-5m",
            "semis_5_15": "Perchis 5m-15cm"
            }
        reg_manager.fields.add_value_map('REG_STADE', {'map': [{str(value): str(descr)} for descr, value in stades.items()]})

        # REG_ETAT
        etats = {
            "continue_sup_80": "Continue >80%",
            "conseqente_50_80": "Conséquente 50-80%",
            "moderee_30_50": "Modérée 30-50%",
            "eparse_10_30": "Eparse 10-30%",
            "infime_inf_10": "Infime <10%"}
        reg_manager.fields.add_value_map('REG_ETAT', {'map': [{str(value): str(descr)} for descr, value in etats.items()]})

    @staticmethod
    def _configure_essence_field(layer_manager, essence_field, essence_secondaire_field, essences_manager, codes, with_variation = False, selected_field = "selected"):
        # This function is quite complicated with a lot of parameter because i need to deal with variation or not and with codes input (GHA/TRANSECT vs TAILLIS).
        # TO-DO : I can surely divide this into piece

        # Build expression
        codes_string = ", ".join([f"'{code}'" for code in codes])
        selected_code_query = f"code IN ({codes_string})"
        unselected_code_query = f"code NOT IN ({codes_string})"

        essences_list = dict()
        for ess in essences_manager.layer.getFeatures(QgsFeatureRequest(QgsExpression(selected_code_query))):
            label = ess['code']
            if with_variation:
                label = f"{ess['code']}{' ' + ess['variation'] if ess['variation'] else ''}"
            essences_list[label] = ess['fid']
        layer_manager.fields.add_value_map(essence_field, {'map': essences_list})

        # 2. Ensure "selected" field for secondary essences
        if selected_field not in [f.name() for f in essences_manager.layer.fields()]:
            essences_manager.fields.add_field(selected_field, QVariant.Bool)

        # 3. Mark secondary essences as selected
        essences_manager.fields.set_field_value_by_expression(selected_field, True, unselected_code_query)

        # 4. Add value relation for ESSENCE_SECONDAIRE_ID
        expression = f'"{selected_field}" = True' if with_variation else f'"{selected_field}" = True AND "variation" IS NULL'

        config = {
            'FilterExpression': expression,
            'Key': 'fid',
            'Layer': essences_manager.layer.id(),
            'Value': 'essence_variation',
            'AllowNull': True
        }
        layer_manager.fields.add_value_relation(essence_secondaire_field, config)

        # 5. Constrain ESSENCE_ID & ESSENCE_SECONDAIRE_ID
        ess_expr = f"""
        ((COALESCE("{essence_field}", '') <> '') AND "{essence_secondaire_field}" IS NULL)
        OR
        ((COALESCE("{essence_field}", '') = '') AND "{essence_secondaire_field}" IS NOT NULL)
        """
        msg = "Veuillez sélectionner une valeur pour ESSENCE ou ESSENCE_SECONDAIRE (mais pas les deux)."
        layer_manager.fields.set_constraint_expression(essence_field, ess_expr, msg, QgsFieldConstraints.ConstraintStrengthHard)

        return None

    def _package_for_qfield(self):
        forest_prefix = get_project_variable("forest_prefix")
        codes = "_".join(self.codes)
        filename = f"EXP_{forest_prefix}_D{self.dmax}H{self.hmax}_{codes}" if forest_prefix else f"D{self.dmax}H{self.hmax}_{codes}"
        
        package_for_qfield(iface, self.project, self.output_dir, filename)

