from ..load.diagnostic_load import DiagnosticLoad
from qsequoia2.modules.utils.seq_config import (
    resolve_seq_layer,
    seq_field,
    seq_read,
)
from ....utils.message import messageLog
from ....utils.variable import get_project_variable
from qgis.core import QgsProject, QgsVariantUtils
from qgis.PyQt.QtWidgets import QMessageBox

class DiagnosticExtract:
    def __init__(self):
        # Unités d'analyse
        self.seq_dir = get_project_variable("QS2_seq_dir")
        seq_id = get_project_variable("QS2_seq_id")
        self.ua = resolve_seq_layer("v.seq.ua", QgsProject.instance(), seq_id=seq_id)
        if self.ua is None:
            self.ua = seq_read("v.seq.ua", self.seq_dir, add_to_project=True)

        # Diagnostic
        self.layers = DiagnosticLoad().load()
        self.pla = self.layers.get("Placette")
        self.gha = self.layers.get("Gha")
        self.va = self.layers.get("Va")
        self.tse = self.layers.get("Tse")
        self.essences = self.layers.get("Essences")

    def extract(self):
        if self.pla is None or self.ua is None:
            return False

        # PEUPLEMENT
        pla_field = "PLT_TYPE"
        ua_field = seq_field("std_type")["name"]
        if not self.extract_field(pla_field, ua_field):
            messageLog("[EXTRACT FIELD] Aucune modification appliquée.")
            QMessageBox.warning(
                None,
                "Extraction du champ échouée",
                f"L'extraction du champ placette {pla_field} vers ua {ua_field} a échoué.")
            return False

        # RICHESSE
        pla_field = "PLT_RICH"
        ua_field = seq_field("std_wealth")["name"]
        if not self.extract_field(pla_field, ua_field):
            messageLog("[EXTRACT FIELD] Aucune modification appliquée.")
            QMessageBox.warning(
                None,
                "Extraction du champ échouée",
                f"L'extraction du champ placette {pla_field} vers ua {ua_field} a échoué.")
            return False

        # STADE
        pla_field = "PLT_STADE"
        ua_field = seq_field("std_stage")["name"]
        if not self.extract_field(pla_field, ua_field):
            messageLog("[EXTRACT FIELD] Aucune modification appliquée.")
            QMessageBox.warning(
                None,
                "Extraction du champ échouée",
                f"L'extraction du champ placette {pla_field} vers ua {ua_field} a échoué.")
            return False

        # SINISTRE
        pla_field = "PLT_SINISTRE"
        ua_field = seq_field("is_damaged")["name"]
        if not self.extract_field(pla_field, ua_field):
            messageLog("[EXTRACT FIELD] Aucune modification appliquée.")
            QMessageBox.warning(
                None,
                "Extraction du champ échouée",
                f"L'extraction du champ placette {pla_field} vers ua {ua_field} a échoué.")
            return False
        
        # TSE_NATURE
        pla_field = "TSE_NATURE"
        ua_field = seq_field("cop_nature")["name"]
        if not self.extract_field(pla_field, ua_field):
            messageLog("[EXTRACT FIELD] Aucune modification appliquée.")
            QMessageBox.warning(
                None,
                "Extraction du champ échouée",
                f"L'extraction du champ placette {pla_field} vers ua {ua_field} a échoué.")
            return False

        # TSE_DENSITE
        pla_field = "TSE_DENS"
        ua_field = seq_field("cop_density")["name"]
        if not self.extract_field(pla_field, ua_field):
            messageLog("[EXTRACT FIELD] Aucune modification appliquée.")
            QMessageBox.warning(
                None,
                "Extraction du champ échouée",
                f"L'extraction du champ placette {pla_field} vers ua {ua_field} a échoué.")
            return False

        # CLOISONNEMENT
        if not self.extract_cloiso():
            messageLog("[EXTRACT CLOISO] Aucune modification appliquée.")
            return False

        # ESSENCES
        if not self.extract_res_ess():
            messageLog("[EXTRACT ESSENCES] Aucune modification appliquée.")
            return False

        # ESSENCES TAILLIS
        if not self.extract_tse_ess():
            messageLog("[EXTRACT TSE] Aucune modification appliquée.")
            return False

        return True

    def extract_field(self, pla_field_name, ua_field_name):
        pla_field_index = self.pla.fields().indexFromName(pla_field_name)
        ua_field_index = self.ua.fields().indexFromName(ua_field_name)
        if pla_field_index == -1 or ua_field_index == -1:
            return False

        changes = {}
        for ua_f in self.ua.getFeatures():
            ua_geom = ua_f.geometry()

            values = set()
            for pla_f in self.pla.getFeatures():
                if ua_geom.intersects(pla_f.geometry()):
                    values.add(pla_f[pla_field_index])

            if len(values) == 1:
                # next(iter(values)) permet de récupérer la valeur du set
                changes[ua_f.id()] = next(iter(values))

        if not changes:
            return False

        already_editing = self.ua.isEditable()
        if not already_editing and not self.ua.startEditing():
            return False

        # Update UA
        for f_id, value in changes.items():
            messageLog(f"[EXTRACT FIELD] Mise à jour de l'UA {f_id} avec la valeur {value}")
            if not self.ua.changeAttributeValue(f_id, ua_field_index, value):
                self.ua.rollBack()
                return False

        if not already_editing and not self.ua.commitChanges():
          self.ua.rollBack()
          return False

        messageLog(f"[EXTRACT FIELD] {len(changes)} UA modifiée(s) : {changes}")
        self.ua.triggerRepaint()
        return True

    def extract_res_ess(self):
        if self.gha is None or self.essences is None:
            return False

        field_1 = self.ua.fields().indexFromName(seq_field("res_spe1")["name"])
        field_2 = self.ua.fields().indexFromName(seq_field("res_spe2")["name"])
        if field_1 == -1 or field_2 == -1:
            return False

        codes = {f["fid"]: f["code"]for f in self.essences.getFeatures()}

        gha_by_placette = {}
        for f in self.gha.getFeatures():
            essence_id = int(f["GHA_ESS"])
            if essence_id not in codes:
                continue

            totals = gha_by_placette.setdefault(f["UUID"], {})
            totals[essence_id] = (totals.get(essence_id, 0) + (f["GHA_G"] or 0))


        messageLog(f"[EXTRACT RES ESSENCES] totals des gha_by_placette: {gha_by_placette}")

        changes = {}
        for ua_f in self.ua.getFeatures():
            totals = {}
            for pla_feature in self.pla.getFeatures():
                if not ua_f.geometry().intersects(pla_feature.geometry()):
                    continue

                for essence_id, gha_sum in gha_by_placette.get(pla_feature["UUID"], {}).items():
                    totals[essence_id] = totals.get(essence_id, 0) + gha_sum

            top = sorted(totals, key=totals.get, reverse=True)[:2]
            if top:
                changes[ua_f.id()] = (codes[top[0]], codes[top[1]] if len(top) > 1 else None)

        if not changes:
            return False

        already_editing = self.ua.isEditable()
        if not already_editing and not self.ua.startEditing():
            return False

        for feature_id, (species_1, species_2) in changes.items():
            if not (
                self.ua.changeAttributeValue(feature_id, field_1, species_1)
                and self.ua.changeAttributeValue(feature_id, field_2, species_2)
            ):
                if not already_editing:
                    self.ua.rollBack()
                return False

        if not already_editing and not self.ua.commitChanges():
            self.ua.rollBack()
            return False

        messageLog(
            f"[EXTRACT RES ESSENCES] {len(changes)} UA modifiée(s) : {changes}"
        )
        self.ua.triggerRepaint()
        return True

    def extract_va_ess(self):
        if self.va is None or self.essences is None:
            return False

        field_1 = self.ua.fields().indexFromName(seq_field("reg_spe1")["name"])
        field_2 = self.ua.fields().indexFromName(seq_field("reg_spe2")["name"])
        if field_1 == -1 or field_2 == -1:
            return False

        codes = {f["fid"]: f["code"]for f in self.essences.getFeatures()}

        va_by_placette = {}
        for f in self.va.getFeatures():
            essence_id = int(f["VA_ESS"])
            if essence_id not in codes:
                continue

            totals = va_by_placette.setdefault(f["UUID"], {})
            totals[essence_id] = (totals.get(essence_id, 0) + (f["VA_TX_HA"] or 0))


        messageLog(f"[EXTRACT VA ESS] totals des va_by_placette: {va_by_placette}")

        changes = {}
        for ua_f in self.ua.getFeatures():
            totals = {}
            for pla_feature in self.pla.getFeatures():
                if not ua_f.geometry().intersects(pla_feature.geometry()):
                    continue

                for essence_id, va_sum in va_by_placette.get(pla_feature["UUID"], {}).items():
                    totals[essence_id] = totals.get(essence_id, 0) + va_sum

            top = sorted(totals, key=totals.get, reverse=True)[:2]
            if top:
                changes[ua_f.id()] = (codes[top[0]], codes[top[1]] if len(top) > 1 else None)

        if not changes:
            return False

        already_editing = self.ua.isEditable()
        if not already_editing and not self.ua.startEditing():
            return False

        for feature_id, (species_1, species_2) in changes.items():
            if not (
                self.ua.changeAttributeValue(feature_id, field_1, species_1)
                and self.ua.changeAttributeValue(feature_id, field_2, species_2)
            ):
                if not already_editing:
                    self.ua.rollBack()
                return False

        if not already_editing and not self.ua.commitChanges():
            self.ua.rollBack()
            return False

        messageLog(
            f"[EXTRACT VA ESSENCES] {len(changes)} UA modifiée(s) : {changes}"
        )
        self.ua.triggerRepaint()
        return True

    def extract_tse_ess(self):
        if self.tse is None or self.essences is None:
            return False

        field_1 = self.ua.fields().indexFromName(seq_field("cop_spe1")["name"])
        field_2 = self.ua.fields().indexFromName(seq_field("cop_spe2")["name"])
        if field_1 == -1 or field_2 == -1:
            return False

        codes = {f["fid"]: f["code"] for f in self.essences.getFeatures()}

        tse_by_placette = {}
        for f in self.tse.getFeatures():
            essence_id = int(f["TSE_ESS"])
            if essence_id not in codes:
                continue

            essence_ids = tse_by_placette.setdefault(f["UUID"], [])
            if essence_id not in essence_ids:
                essence_ids.append(essence_id)

        changes = {}
        for ua_f in self.ua.getFeatures():
            essence_ids = []
            for pla_feature in self.pla.getFeatures():
                if not ua_f.geometry().intersects(pla_feature.geometry()):
                    continue

                for essence_id in tse_by_placette.get(pla_feature["UUID"], []):
                    if essence_id not in essence_ids:
                        essence_ids.append(essence_id)

            if essence_ids:
                changes[ua_f.id()] = (
                    codes[essence_ids[0]],
                    codes[essence_ids[1]] if len(essence_ids) > 1 else None,
                )

        if not changes:
            return False

        already_editing = self.ua.isEditable()
        if not already_editing and not self.ua.startEditing():
            return False

        for feature_id, (species_1, species_2) in changes.items():
            if not (
                self.ua.changeAttributeValue(feature_id, field_1, species_1)
                and self.ua.changeAttributeValue(feature_id, field_2, species_2)
            ):
                if not already_editing:
                    self.ua.rollBack()
                return False

        if not already_editing and not self.ua.commitChanges():
            self.ua.rollBack()
            return False

        messageLog(
            f"[EXTRACT tse ESSENCES] {len(changes)} UA modifiée(s) : {changes}"
        )
        self.ua.triggerRepaint()
        return True

    def extract_cloiso(self):
        if self.pla is None or self.ua is None:
            return False

        pla_field = self.pla.fields().indexFromName("PLT_CLOISO")
        ua_field = self.ua.fields().indexFromName(seq_field("is_compartmented")["name"])
        if pla_field == -1 or ua_field == -1:
            return False

        changes = {}
        for ua_f in self.ua.getFeatures():
            value = False
            for pla_f in self.pla.getFeatures():
                pla_value = pla_f[pla_field]
                if (
                    ua_f.geometry().intersects(pla_f.geometry())
                    and not QgsVariantUtils.isNull(pla_value)
                    and pla_value != ""
                ):
                    value = True
                    break

            changes[ua_f.id()] = value

        if not changes:
            return False

        already_editing = self.ua.isEditable()
        if not already_editing and not self.ua.startEditing():
            return False

        for feature_id, value in changes.items():
            if not self.ua.changeAttributeValue(feature_id, ua_field, value):
                if not already_editing:
                    self.ua.rollBack()
                return False

        if not already_editing and not self.ua.commitChanges():
            self.ua.rollBack()
            return False

        messageLog(f"[EXTRACT CLOISO] {len(changes)} UA modifiée(s).")
        self.ua.triggerRepaint()
        return True
