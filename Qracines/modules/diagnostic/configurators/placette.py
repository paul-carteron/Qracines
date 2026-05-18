from qgis.core import QgsFieldConstraints
from ....core.layer import FormBuilder, FieldEditor
from ....utils.config import get_peuplements
from config import stade, richesse, structure, tx_trouee, veg_con, tx_deg, protect, sanitaire, cloiso, mecanisable, densite, tse_vol

class PlacetteConfigurator:

    def __init__(self, layer, relations):
        self.layer = layer
        self.relations = relations
        self.fb = FormBuilder(layer)
        self.fe = FieldEditor(layer)

    def configure(self):
        print("configure PLACETTE layer")
        self._init_form()
        self._configure_fields()
        self._style()

    def _init_form(self):
        
        self.fb.init_form()

        # ve: stand for visibility_expression
        self.forest_plt = "('FRF', 'FIF', 'FRM', 'FIM', 'FRR', 'FIR', 'PEU', 'MFT', 'MRT', 'MMT', 'TSB', 'TSN', 'REC')"
        self.va_plt = "('REF', 'PLF', 'REM', 'PLM', 'RER', 'PLR')"

        forest_ve = f"\"PLT_TYPE\" IN {self.forest_plt}"
        va_ve = f"\"PLT_TYPE\" IN {self.va_plt}"
        both = f"{va_ve} OR {forest_ve}"

        # GENERAL
        general_tab = self.fb.create_tab("Général")
        group = self.fb.create_group("", parent = general_tab, columns=2)
        self.fb.new_add_fields(["COMPTEUR", "PLT_PARCELLE"], parent = group)
        self.fb.new_add_fields(["PLT_TYPE", "PLT_STADE", "PLT_AME", "PLT_RMQ", "PLT_PHOTO"], parent = general_tab)

        # PEUPLEMENT
        tab_peupl = self.fb.create_tab("Peuplement")
        self.fb.new_add_relation(self.relations["Gha"], tab_peupl, visibility_expression=forest_ve)
        self.fb.new_add_fields(["PLT_RICH", "PLT_STRUCTURE", "PLT_DMOY", "PLT_CLOISO", "PLT_ELAG", "PLT_SANIT", "PLT_MECA"], parent = tab_peupl)
        group = self.fb.create_group("", parent = tab_peupl, columns=2)
        self.fb.new_add_fields(["PLT_SINISTRE", "PLT_ACCESS"], parent = group)

        # TAILLIS
        tab_taillis = self.fb.create_tab("Taillis")
        self.fb.new_add_relation(self.relations["Tse"], tab_taillis, visibility_expression=both)
        self.fb.new_add_fields(["TSE_DENS", "TSE_VOL", "TSE_NATURE"], parent = tab_taillis)

        # REGE
        rege_taillis = self.fb.create_tab("Régé")
        self.fb.new_add_relation(self.relations["Reg"], rege_taillis, visibility_expression=forest_ve)

        # RENOUVELLEMENT
        tab_va = self.fb.create_tab("Renouvellement")
        self.fb.new_add_relation(self.relations["Va"], tab_va, visibility_expression=va_ve)
        self.fb.new_add_fields(["VA_HT", "PLT_ELAG", "VA_TX_TROUEE", "VA_VEG_CON", "VA_TX_DEG", "VA_PROTECT"], parent = tab_va)

        # Apply to layer
        self.fb.apply()

    def _configure_fields(self):
        
        # region GLOBAL
        # ALIASES
        aliases = [
            ("COMPTEUR", "Placette n°"),
            ("PLT_PARCELLE", "PRF/SPRF"),
            ("PLT_TYPE", "Type de peuplement"),
            ("PLT_STADE", "Stade"),
            ("PLT_AME", "Aménagement"), 
            ("PLT_RMQ", "Remarque"), 
            ("PLT_PHOTO", "Photo"),
            # PEUPLEMENT
            ("PLT_RICH", "Richesse"),
            ("PLT_STRUCTURE", "Structure"),
            ("PLT_DMOY", "Diamètre Moyen (cm)"),
            ("PLT_ELAG", "Élagage"), 
            ("PLT_SANIT", "Sanitaire"), 
            ("PLT_CLOISO", "Cloisonnement"), 
            ("PLT_MECA", "Mécanisation"),
            ("PLT_SINISTRE", "Peuplement sinistré ?"),
            ("PLT_ACCESS", "Peuplement accessible ?"),
            # RENOUVELLEMENT
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
            self.fe.set_alias(field, alias)

        # UUID
        # If apply_on_update=True, uuid() resets on each children edit: 
        # - Create parent → UUID=A 
        # - Add first child → FK=A 
        # - Edit another child → UUID becomes B (child’s FK=A breaks under Composition) 
        # - Add second child → FK=B 
        # Only the last child stays linked. Using apply_on_update=False keeps the UUID stable so all children link correctly.
        field_name = "UUID"
        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintUnique)
        self.fe.set_default_value(field_name, "uuid()", apply_on_update=False)
        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)

        # COMPTEUR
        field_name = "COMPTEUR"
        self.fe.set_read_only(field_name)
        self.fe.set_default_value(field_name, 'count("fid") + 1')

        # PLT_PARCELLE
        self.fe.set_constraint("PLT_PARCELLE", QgsFieldConstraints.ConstraintNotNull)

        # PLT_TYPE
        field_name = "PLT_TYPE"
        peuplements = get_peuplements()
        self.fe.add_value_map(field_name, {'map': [{str(name): str(code)} for code, name in peuplements.items()]})
        self.fe.set_constraint(field_name, QgsFieldConstraints.ConstraintNotNull)

        # PLT_STADE
        field_name = 'PLT_STADE'
        self.fe.add_value_map(field_name, {'map': [{str(name): str(code)} for code, name in stade.items()]})
        c_exp = f'''
        ("PLT_TYPE" IN {tuple(get_peuplements("non_forestier"))} AND ("{field_name}" IS NULL OR "{field_name}" = ''))
        OR
        ("PLT_TYPE" IN {tuple(get_peuplements("renouvellement"))} AND "{field_name}" IN ('SFO','GPE'))
        OR
        ("PLT_TYPE" IN {tuple(get_peuplements("futaie"))} AND "{field_name}" IN ('RSF','RGP','JEU','ADU','MAT'))
        OR
        ("PLT_TYPE" IN {tuple(get_peuplements("taillis"))} AND "{field_name}" IN ('EXP','NEX'))
        '''
        description = "Le stade dépend du type de peuplements, ex: 'SFO' ou 'GPE' pour les renouvellements."
        self.fe.set_constraint_expression(field_name, c_exp, description, strength=QgsFieldConstraints.ConstraintStrengthHard)

        # PLT_PHOTO
        self.fe.add_external_resource("PLT_PHOTO")

        # endregion

        # region PEUPLEMENT
        # PLT_RICH
        field_name = 'PLT_RICH'
        self.fe.add_value_map(field_name, {'map': [{str(name): str(code)} for code, name in richesse.items()]})
        c_exp = f'''
        ("PLT_TYPE" NOT IN {tuple(get_peuplements("futaie", "taillis"))})
        OR
        ("{field_name}" IS NOT NULL AND "{field_name}" <> '')
        '''
        self.fe.set_constraint_expression(field_name, c_exp, f"Le champ {field_name} doit être rempli pour les futaies ou taillis.")

        # PLT_STRUCTURE
        self.fe.add_value_map('PLT_STRUCTURE', {'map': [{str(name): str(code)} for code, name in structure.items()]}, allow_null=True)

        # PLT_DMOY
        self.fe.add_value_map('PLT_DMOY', {'map': [{str(d): str(d)} for d in range(10, 150 + 1, 5)]})

        # PLT_ELAG
        elagage = {'2m':'2m', '4m': '4m', '6m': '6m'}
        self.fe.add_value_map('PLT_ELAG', {'map': [{str(name): str(code)} for code, name in elagage.items()]})

        # PLT_SANIT
        self.fe.add_value_map('PLT_SANIT', {'map': [{str(name): str(code)} for code, name in sanitaire.items()]})

        # PLT_CLOISO
        self.fe.add_value_map('PLT_CLOISO', {'map': [{str(name): str(code)} for code, name in cloiso.items()]})

        # PLT_MECA
        self.fe.add_value_map('PLT_MECA', {'map': [{str(name): str(code)} for code, name in mecanisable.items()]})

        # PLT_SINISTRE 
        self.fe.set_default_value("PLT_SINISTRE", "FALSE")

        # PLT_ACCESS 
        self.fe.set_default_value("PLT_ACCESS", "FALSE")

        # endregion

        # region RENOUVELLEMENT
        # VA_HT
        self.fe.add_value_map('VA_HT', {'map': [{str(h): str(h)} for h in [0.5, 1, 1.5, 2, 2.5] + list(range(3, 15 + 1))]})

        # VA_TX_TROUEE
        self.fe.add_value_map('VA_TX_TROUEE', {'map': [{str(name): str(code)} for code, name in tx_trouee.items()]})

        # VA_VEG_CON
        self.fe.add_value_map('VA_VEG_CON', {'map': [{str(name): str(code)} for code, name in veg_con.items()]})

        # VA_TX_DEG
        self.fe.add_value_map('VA_TX_DEG', {'map': [{str(name): str(code)} for code, name in tx_deg.items()]})

        # VA_PROTECT
        self.fe.add_value_map('VA_PROTECT', {'map': [{str(name): str(code)} for code, name in protect.items()]})
        # endregion

        # region TAILLIS
        # TSE_DENS
        self.fe.add_value_map(
            'TSE_DENS',
            {'map': [{str(name): str(code)} for code, name in densite.items()]},
            allow_null=True
        )

        # TSE_VOL
        self.fe.add_value_map(
            'TSE_VOL',
            {'map': [{str(name): str(code)} for code, name in tse_vol.items()]},
            allow_null=True
        )

        # TSE_NATURE
        nature = {
            "BI_BE" : "BI/BE", 
            "BC" : "BC"
        }
        self.fe.add_value_map(
            'TSE_NATURE',
            {'map': [{str(name): str(code)} for code, name in nature.items()]},
            allow_null=True
        )
        
        # endregion
        return None
    
    def _style(self):
        s = self.layer.renderer().symbol()
        s.symbolLayer(0).setSize(3)
        self.layer.triggerRepaint()

    def _set_qfield_properties(self):
        
        # Peuplement ou Dmoy ne doivent pas être sous forme de bouton
        treshold = min(
            len(get_peuplements()),
            len(range(10, 150 + 1, 5))
        )
        
        self.layer.setCustomProperty("QFieldSync/value_map_button_interface_threshold", treshold)