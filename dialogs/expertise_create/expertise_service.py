import processing

from qgis.core import (
    QgsProject,
    QgsProcessing,
    QgsFieldConstraints,
    QgsFeatureRequest,
    QgsExpression,
    QgsRendererCategory,
    QgsCategorizedSymbolRenderer,
    QgsSymbol,
    QgsWkbTypes,
    QgsSimpleLineSymbolLayer,
    QgsMapLayer
)

from qgis.utils import iface
from qgis.PyQt.QtCore import Qt

from PyQt5.QtCore import QVariant
from PyQt5.QtGui import QColor

from ...core.layer_factory import LayerFactory
from ...core.layer.manager import FormBuilder, FieldEditor
from ...utils.config import get_peuplements, get_limites, get_limites_config
from ...utils.layers import load_gpkg, create_relation, load_vectors
from ...utils.utils import fold, unfold

class ExpertiseService:

    def __init__(
        self,
        codes: list,
        codes_taillis: list,
        dmin: int,
        dmax: int,
        hmin: int,
        hmax: int,
        essences_layer: dict,
        grid_controller,
        raster_controller
    ):
        self.iface = iface
        self.project = QgsProject.instance()
        self.root = self.project.layerTreeRoot()
        self.codes = codes
        self.codes_taillis = codes_taillis
        self.dmin, self.dmax = dmin, dmax
        self.hmin, self.hmax = hmin, hmax
        self.essences_layer = essences_layer
        self.grid_controller = grid_controller
        self.raster_controller = raster_controller

    def run(self):
        """
        Runs the full workflow. 
        Returns the output_dir path (as str) if packaging was done, otherwise None.
        Raises on any error.
        """
        layers = {
            layer_name: LayerFactory.create(layer_name, "EXPERTISE")
            for layer_name in LayerFactory.get_layer_names("EXPERTISE")
        }

        layers["essences"] = self.essences_layer

        if self.grid_controller.is_valid():
            layers["grid"] = self.grid_controller.create_grid()

        self.project.addMapLayers(list(layers.values()), addToLegend=False)

        relations = {
            "gha": create_relation(layers["placette"], layers["gha"], "UUID", "UUID"),
            "tse": create_relation(layers["placette"], layers["tse"], "UUID", "UUID"),
            "va":  create_relation(layers["placette"], layers["va"], "UUID", "UUID"),
            "reg": create_relation(layers["placette"], layers["reg"], "UUID", "UUID"),
        }

        # PLACETTE
        placette = layers["placette"]
        self._init_placette_form(placette, relations)
        self._configure_placette(placette)
        placette.setCustomProperty("QFieldSync/value_map_button_interface_threshold", 13)

        # TRANSECT
        print("configure TRANSECT layer")
        transect = layers["transect"]
        essences = layers["essences"]
        self._init_transect_form(transect)
        self._configure_transect(transect, self.dmin, self.dmax, self.hmin, self.hmax)
        self._configure_essence_field(transect, "TR_ESSENCE_ID", "TR_ESSENCE_SECONDAIRE_ID", essences, self.codes, with_variation = True)
        transect.layer.setCustomProperty("QFieldSync/value_map_button_interface_threshold", 99)

        # LIMITE
        print("configure LIMITE layer")
        limite = layers["limite"]
        self._init_limite_form(limite)
        self._configure_limite(limite)
        self._style_limite(limite)

        # GHA
        print("configure GHA layer")
        gha = layers["gha"]
        self._init_gha_form(gha)  
        self._configure_gha(gha)  
        self._configure_essence_field(gha, "GHA_ESSENCE_ID", "GHA_ESSENCE_SECONDAIRE_ID", essences, self.codes, with_variation = False)
        gha.setCustomProperty("QFieldSync/value_map_button_interface_threshold", 99)

        # # TAILLIS
        print("configure TAILLIS layer")
        tse = layers["tse"]
        self._init_tse_form(tse)  
        self._configure_tse(tse)  
        self._configure_essence_field(tse, "TSE_ESSENCE_ID", "TSE_ESSENCE_SECONDAIRE_ID", essences, self.codes_taillis, with_variation = False, selected_field = "selected_taillis")
        tse.layer.setCustomProperty("QFieldSync/value_map_button_interface_threshold", 99)

        # VALEUR AVENIR
        print("configure VALEUR AVENIR layer")
        va = layers["va"]
        self._init_va_form(va)  
        self._configure_va(va)  
        self._configure_essence_field(va, "VA_ESSENCE_ID", "VA_ESSENCE_SECONDAIRE_ID", essences, self.codes, with_variation = False)
        va.layer.setCustomProperty("QFieldSync/value_map_button_interface_threshold", 99)

        # REGENERATION
        print("configure REGENERATION layer")
        reg = layers["reg"]
        self._init_reg_form(reg)  
        self._configure_reg(reg)  
        self._configure_essence_field(reg, "REG_ESSENCE_ID", "REG_ESSENCE_SECONDAIRE_ID", essences, self.codes, with_variation = False)
        reg.layer.setCustomProperty("QFieldSync/value_map_button_interface_threshold", 99)

        result = processing.run("native:package", {
            'LAYERS':      list(layers.values()),
            'OUTPUT':      QgsProcessing.TEMPORARY_OUTPUT,
            'OVERWRITE':   True,
            'SAVE_STYLES': True,
            'EXPORT_RELATED_LAYERS': True
        })

        self.gpkg_path = result['OUTPUT']
        loaded_layers = load_gpkg(self.gpkg_path, group_name="DIAGNOSTIC")

        for layer in loaded_layers:
            if layer.geometryType() == QgsWkbTypes.NullGeometry:
                flags = layer.flags()
                flags |= QgsMapLayer.Private
                layer.setFlags(flags)

        load_vectors("parca_polygon_occup", group_name= "VECTEUR")

        self.raster_controller.load_selected_rasters()

        fold()
        unfold("EXPERTISE")

        return self.gpkg_path
    
    
    @staticmethod
    def _init_placette_form(placette, relations):

        placette_fb = FormBuilder(placette)

        placette_fb.init_form()

        # ve: stand for visibility_expression
        forest_plt = "('FRF', 'FIF', 'REF', 'PLF', 'FRM', 'FIM', 'REM', 'PLM', 'FRR', 'FIR', 'RER', 'PLR', 'PEU', 'MFT', 'MRT', 'MMT', 'TSB', 'TSN')"
        va_plt = "('REF', 'PLF', 'REM', 'PLM', 'RER', 'PLR')"

        forest_ve = f"\"PLTM_TYPE\" IN {forest_plt}"
        va_ve = f"\"PLTM_TYPE\" IN {va_plt}"
        
        general_tab = placette_fb.create_tab("Général")
        placette_fb.new_add_fields(["COMPTEUR"], parent = general_tab)
        group = placette_fb.create_group("Localisation", parent = general_tab, columns=2)
        placette_fb.new_add_fields(["PLTM_PARCELLE", "PLTM_STRATE"], parent = group)
        placette_fb.new_add_fields(["PLTM_TYPE", "PLA_RMQ"], parent = general_tab)

        placette_fb.new_add_relation(relations["gha"], parent=general_tab, visibility_expression = forest_ve)
        placette_fb.new_add_fields(["TSE_STERE_HA"], parent=general_tab)
        placette_fb.new_add_relation(relations["tse"], parent=general_tab, visibility_expression = forest_ve)
        placette_fb.new_add_relation(relations["va"], parent=general_tab, visibility_expression = va_ve)
        placette_fb.new_add_relation(relations["reg"], parent=general_tab, visibility_expression = forest_ve)

        placette_fb.apply()

    @staticmethod
    def _configure_placette(placette):
        placette_f = FieldEditor(placette)

        # ALIASES
        aliases = [
            ("COMPTEUR", "Placette"),
            ("PLTM_PARCELLE", "Parcelle"),
            ("PLTM_STRATE", "Strate"),
            ("PLA_RMQ", "Remarque"),
            ("PLTM_TYPE", "Type de peuplement"),
            ("TSE_STERE_HA", "Taillis [st/ha]")]
        
        for field, alias in aliases:
            placette_f.set_alias(field, alias)

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

        # PLTM_PARCELLE & PLTM_STRATE
        expression = '"PLTM_PARCELLE" is not NULL OR "PLTM_STRATE" is not NULL'
        description = "Ajouter une parcelle ou une strate si l'inventaire n'utilise pas de carto"
        placette_f.set_constraint_expression("PLTM_PARCELLE", expression, description)
        placette_f.set_constraint_expression("PLTM_STRATE", expression, description)
        placette_f.set_reuse_last_value ("PLTM_PARCELLE")
        placette_f.set_reuse_last_value("PLTM_STRATE")

        # PLTM_TYPE
        peuplements = get_peuplements()
        placette_f.add_value_map('PLTM_TYPE', {'map': [{str(name): str(code)} for code, name in peuplements.items()]})

        # TSE_STERE_HA
        stere_ha = [*range(0, 200, 25), *range(200, 400, 50)]
        placette_f.add_value_map("TSE_STERE_HA", {'map': [{str(value): str(value)} for value in stere_ha]})

        # RELATIONS
        ## This line has to be after all fields are configured
        # placette_f.set_relation_label("gha", label = False)
        # placette_f.set_relation_label("tse", label = "Essence taillis")
        # placette_f.set_relation_label("va", label = False)
        # placette_f.set_relation_label("reg", label = False)

        return None

    @staticmethod
    def _init_transect_form(transect):
        transect_fb = FormBuilder(transect)
        transect_fb.init_form()
        transect_fb.new_add_fields(["TR_PARCELLE", "TR_STRATE", "TR_ESSENCE_ID", "TR_ESSENCE_SECONDAIRE_ID", "TR_DIAMETRE", "TR_EFFECTIF", "TR_HAUTEUR"])
        transect_fb.apply()
    
    @staticmethod
    def _configure_transect(transect, dmin, dmax, hmin, hmax):
        transect_f = FieldEditor(transect)

        # ALIASES
        aliases = [
            ("TR_PARCELLE", "Parcelle"),
            ("TR_STRATE", "Strate"),
            ("TR_ESSENCE_ID", "Essence"),
            ("TR_ESSENCE_SECONDAIRE_ID", "Autre essence"),
            ("TR_DIAMETRE", "Diamètre [cm]"),
            ("TR_EFFECTIF", "Effectif"),
            ("TR_HAUTEUR", "Hauteur [m]"),]
        
        for field, alias in aliases:
            transect_f.set_alias(field, alias)

        # UUID
        field_name = "UUID"
        transect_f.set_constraint(field_name, QgsFieldConstraints.ConstraintUnique)
        transect_f.set_default_value(field_name, "uuid()", apply_on_update=False)
        transect_f.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)

        # TR_PARCELLE & TR_STRATE
        expression = '"TR_PARCELLE" is not NULL OR "TR_STRATE" is not NULL'
        description = "Ajouter une parcelle ou une strate si l'inventaire n'utilise pas de carto"
        transect_f.set_constraint_expression("TR_PARCELLE", expression, description)
        transect_f.set_constraint_expression("TR_STRATE", expression, description)
        transect_f.set_reuse_last_value ("TR_PARCELLE")
        transect_f.set_reuse_last_value("TR_STRATE")

        # TR_DIAMETRE
        field_name = "TR_DIAMETRE"
        transect_f.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        transect_f.add_value_map(field_name, {'map': [{str(d): str(d)} for d in range(dmin, dmax + 1, 5)]})
        expression = '"TR_DIAMETRE" != \'\''
        description = "Le champ TR_DIAMETRE ne peut pas être vide."
        transect_f.set_constraint_expression(field_name, expression, description ,QgsFieldConstraints.ConstraintStrengthHard)

        # TR_EFFECTIF
        field_name = "TR_EFFECTIF"
        transect_f.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        transect_f.add_range(field_name, {'AllowNull': False, 'Max': 1000, 'Min': 0, 'Precision': 0, 'Step': 1})
        transect_f.set_default_value(field_name, '1', False)

        # TR_HAUTEUR
        field_name = "TR_HAUTEUR"
        transect_f.add_value_map(field_name, {'map': [{str(h): str(h)} for h in range(hmin, hmax + 1)]})

        return None
    
    @staticmethod
    def _init_limite_form(limite):
        limite_fb = FormBuilder(limite)
        limite_fb.init_form()
        limite_fb.new_add_fields(["LIMITE_TYPE", "LIMITE_RMQ"])
        limite_fb.apply()

    @staticmethod
    def _configure_limite(limite):
        limite_f = FieldEditor(limite)

        # ALIASES
        aliases = [
            ("LIMITE_TYPE", "Type"),
            ("LIMITE_RMQ", "Remarque"),
        ]
        
        for field, alias in aliases:
            limite_f.set_alias(field, alias)

        # LIMITE_TYPE
        limites = get_limites()
        limite_f.add_value_map('LIMITE_TYPE', {'map': [{str(name): str(code)} for code, name in limites.items()]})
    
    @staticmethod
    def _style_limite(limite):
        field = 'LIMITE_TYPE'
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
            width = float(props.get("width", 0.6))
            line_type = props.get("style", "solid").lower()
            label = props.get("label", code)

            line_layer = QgsSimpleLineSymbolLayer()
            line_layer.setColor(color)
            line_layer.setWidth(width)
            line_layer.setPenStyle(style_map.get(line_type, Qt.SolidLine))

            symbol = QgsSymbol.defaultSymbol(limite.geometryType())
            symbol.deleteSymbolLayer(0)
            symbol.appendSymbolLayer(line_layer)

            categories.append(QgsRendererCategory(code, symbol, label))

        renderer = QgsCategorizedSymbolRenderer(field, categories)
        limite.setRenderer(renderer)
        limite.triggerRepaint()

    @staticmethod
    def _init_gha_form(gha):
        gha_fb = FormBuilder(gha)
        gha_fb.init_form()
        gha_fb.new_add_fields(["GHA_ESSENCE_ID", "GHA_ESSENCE_SECONDAIRE_ID", "GHA_G"])
        gha_fb.apply()
    
    @staticmethod
    def _configure_gha(gha):
        gha_fe = FieldEditor(gha)
        # ALIASES
        aliases = [
            ("GHA_ESSENCE_ID", "Essence"),
            ("GHA_ESSENCE_SECONDAIRE_ID", "Autre essence"),
            ("GHA_G", "Surface terrière")
        ]
        
        for field, alias in aliases:
            gha_fe.set_alias(field, alias)
        
        # DISPLAY EXPRESSION
        display_expression = """
            WITH_VARIABLE(
                'ess',
                get_feature(
                    'essences',
                    'fid',
                    coalesce(NULLIF("GHA_ESSENCE_ID", ''), "GHA_ESSENCE_SECONDAIRE_ID")
                ),
                concat(attribute(@ess, 'essence_variation'),
                ' : ',
                "GHA_G",
                ' m²/ha ')
            )
            """
        gha.setDisplayExpression(display_expression)

        # GHA_G
        field_name = "GHA_G"
        gha_fe.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        gha_fe.set_constraint_expression(field_name, f'"{field_name}" > 0', "La surface terrière doit être supérieur à 0", strength=QgsFieldConstraints.ConstraintStrengthHard)
        gha_fe.add_range(field_name, {'AllowNull': False, 'Max': 100, 'Min': 0, 'Precision': 0, 'Step': 1})

    @staticmethod
    def _init_tse_form(tse):
        tse_fb = FormBuilder(tse)
        tse_fb.init_form()
        tse_fb.new_add_fields(["TSE_ESSENCE_ID", "TSE_ESSENCE_SECONDAIRE_ID"])
        tse_fb.apply()
    
    @staticmethod
    def _configure_tse(tse):
        tse_fe = FieldEditor(tse)

        # ALIASES
        aliases = [
            ("TSE_ESSENCE_ID", "Essence"),
            ("TSE_ESSENCE_SECONDAIRE_ID", "Autre essence")
        ]
        
        for field, alias in aliases:
            tse_fe.set_alias(field, alias)
        
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
        tse.setDisplayExpression(display_expression)

    @staticmethod
    def _init_va_form(va):
        va_fb = FormBuilder(va)
        va_fb.init_form()
        va_fb.new_add_fields(["VA_ESSENCE_ID", "VA_ESSENCE_SECONDAIRE_ID", "VA_TX_TROUEE", "VA_AGE_APP", "VA_TX_HA", "CUMUL_TX_VA"])
        va_fb.apply()

    @staticmethod
    def _configure_va(va):
        va_f = FieldEditor(va)

        # ALIASES
        aliases = [
            ("VA_ESSENCE_ID", "Essence"),
            ("VA_ESSENCE_SECONDAIRE_ID", "Autre essence"),
            ("VA_AGE_APP", "Age Apparent"),
            ("VA_TX_TROUEE", "Taux trouée [%]"),
            ("VA_TX_HA", "Recouvrement [%]"),
            ("CUMUL_TX_VA", "Cumul des recouvrements"),
        ]
        
        for field, alias in aliases:
            va_f.set_alias(field, alias)
        
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
        va.setDisplayExpression(display_expression)

        # VA_AGE_APP
        field_name = "VA_AGE_APP"
        va_f.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        va_f.set_constraint_expression(field_name, f'"{field_name}" > 0', "L'âge doit être supérieur à 0", strength=QgsFieldConstraints.ConstraintStrengthHard)
        va_f.add_range(field_name, {'AllowNull': False, 'Max': 300, 'Min': 0, 'Precision': 0, 'Step': 1})

        # VA_TX_TROUEE
        va_f.add_range("VA_TX_TROUEE", {'AllowNull': True, 'Max': 100, 'Min': 0, 'Precision': 0, 'Step': 10})

        # VA_TX_HA
        field_name = "VA_TX_HA"
        va_f.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)
        expression = '"CUMUL_TX_VA" + "VA_TX_HA" = 100'
        description = 'La somme de VA_TX_HA et de CUMUL_TX_VA doit être égale à 100.'
        va_f.set_constraint_expression(field_name, expression, description)
        va_f.add_range(field_name, {'AllowNull': False, 'Max': 100, 'Min': 0, 'Precision': 0, 'Step': 10})

        # CUMUL_TX_VA
        field_name = "CUMUL_TX_VA"
        default_value = """aggregate(layer:='va', aggregate:='sum', expression:="VA_TX_HA", filter:="UUID" = attribute(@parent, 'UUID'))"""
        va_f.set_default_value(field_name, default_value)

    @staticmethod
    def _init_reg_form(reg):
        reg_fb = FormBuilder(reg)
        reg_fb.init_form()
        reg_fb.new_add_fields(["REG_ESSENCE_ID", "REG_ESSENCE_SECONDAIRE_ID", "REG_STADE", "REG_ETAT"])
        reg_fb.apply()
    
    @staticmethod
    def _configure_reg(reg):
        reg_fe = FieldEditor(reg)

        # ALIASES
        aliases = [
            ("REG_ESSENCE_ID", "Essence"),
            ("REG_ESSENCE_SECONDAIRE_ID", "Autre essence"),
            ("REG_STADE", "Stade"),
            ("REG_ETAT", "Etat"),
        ]
        
        for field, alias in aliases:
            reg_fe.set_alias(field, alias)

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
        reg.setDisplayExpression(display_expression)

        # REG_STADE
        stades = {
            "semis_inf_05": "Semis <0.5m",
            "semis_05_1": "Semis 0.5-1m",
            "fourre_1_3": "Fourré 1-3m",
            "semis_3_5": "Gaulis 3-5m",
            "semis_5_15": "Perchis 5m-15cm"
            }
        reg_fe.add_value_map('REG_STADE', {'map': [{str(value): str(descr)} for descr, value in stades.items()]})

        # REG_ETAT
        etats = {
            "continue_sup_80": "Continue >80%",
            "conseqente_50_80": "Conséquente 50-80%",
            "moderee_30_50": "Modérée 30-50%",
            "eparse_10_30": "Eparse 10-30%",
            "infime_inf_10": "Infime <10%"}
        reg_fe.add_value_map('REG_ETAT', {'map': [{str(value): str(descr)} for descr, value in etats.items()]})

    @staticmethod
    def _configure_essence_field(layer, essence_field, essence_secondaire_field, essence_layer, codes, with_variation = False, selected_field = "selected"):
        # This function is quite complicated with a lot of parameter because i need to deal with variation or not and with codes input (GHA/TRANSECT vs TAILLIS).
        # TO-DO : I can surely divide this into piece
        layer_fe = FieldEditor(layer)

        # Build expression
        codes_string = ", ".join([f"'{code}'" for code in codes])
        selected_code_query = f"code IN ({codes_string})"
        unselected_code_query = f"code NOT IN ({codes_string})"

        essences_list = dict()
        for ess in essence_layer.getFeatures(QgsFeatureRequest(QgsExpression(selected_code_query))):
            label = ess['code']
            if with_variation:
                if ess['variation'] in ('foudroyé', 'nécrosé', 'dépérissant'):
                    continue # Exclude these variations
                label = f"{ess['code']}{' ' + ess['variation'] if ess['variation'] else ''}"
            # Avoid overwriting in case of ess whith multiple variation
            if label not in essences_list:
                essences_list[label] = ess['fid']
        layer_fe.add_value_map(essence_field, {'map': essences_list})

        # 2. Ensure "selected" field for secondary essences
        if selected_field not in [f.name() for f in essence_layer.fields()]:
            layer_fe.add_field(selected_field, QVariant.Bool)

        # 3. Mark secondary essences as selected
        layer_fe.set_field_value_by_expression(selected_field, True, unselected_code_query)

        # 4. Add value relation for ESSENCE_SECONDAIRE_ID
        expression = f'"{selected_field}" = True' if with_variation else f'"{selected_field}" = True AND "variation" IS NULL'

        config = {
            'AllowNull': True,
            'FilterExpression': expression,
            'Key': 'fid',
            'Layer': essence_layer.id(),
            'Value': 'essence_variation'
        }

        layer_fe.add_value_relation(essence_secondaire_field, config)

        # 5. Constrain ESSENCE_ID & ESSENCE_SECONDAIRE_ID
        ess_expr = f"""
        ((COALESCE("{essence_field}", '') <> '') AND "{essence_secondaire_field}" IS NULL)
        OR
        ((COALESCE("{essence_field}", '') = '') AND "{essence_secondaire_field}" IS NOT NULL)
        """
        msg = "Veuillez sélectionner une valeur pour ESSENCE ou ESSENCE_SECONDAIRE (mais pas les deux)."
        layer_fe.set_constraint_expression(essence_field, ess_expr, msg, QgsFieldConstraints.ConstraintStrengthHard)

        return None
