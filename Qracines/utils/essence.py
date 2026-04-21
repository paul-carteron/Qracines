from qgis.core import (
    QgsFieldConstraints,
    QgsVectorLayer,
    QgsField,
    QgsFeature,
    QgsFields
)
from qgis.PyQt.QtCore import QVariant
from pathlib import Path
import json
from ..core.layer import FieldEditor
from .config import get_config_path

_SKIP_VARIATIONS = {"foudroyé", "nécrosé", "dépérissant"}


def load_essences(json_path = get_config_path("essences.json"), name="Essences"):

    json_path = Path(json_path)

    if not json_path.exists():
        raise FileNotFoundError(f"JSON not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # --- define fields (same schema as query) ---
    fields = QgsFields()
    fields.append(QgsField("fid", QVariant.Int))
    fields.append(QgsField("essence", QVariant.String))
    fields.append(QgsField("essence_variation", QVariant.String))
    fields.append(QgsField("code", QVariant.String))
    fields.append(QgsField("variation", QVariant.String))
    fields.append(QgsField("ordre", QVariant.Int))
    fields.append(QgsField("type", QVariant.String))

    # --- create memory layer (no geometry) ---
    layer = QgsVectorLayer("None", name, "memory")
    provider = layer.dataProvider()
    provider.addAttributes(fields)
    layer.updateFields()

    def _to_qgis_null(value):
        if value in ("NULL", "", "None"):
            return None
        return value

    features = []

    for fid_str, attrs in data.items():
        f = QgsFeature()
        f.setFields(fields)

        # convert fid safely
        try:
            fid = int(fid_str)
        except:
            fid = None

        f["fid"] = _to_qgis_null(fid)
        f["essence"] = _to_qgis_null(attrs.get("essence"))
        f["essence_variation"] = _to_qgis_null(attrs.get("essence_variation"))
        f["code"] = _to_qgis_null(attrs.get("code"))
        f["variation"] = _to_qgis_null(attrs.get("variation"))
        f["ordre"] = _to_qgis_null(attrs.get("ordre"))
        f["type"] = _to_qgis_null(attrs.get("type"))

        features.append(f)

    provider.addFeatures(features)

    if not layer.isValid():
        raise RuntimeError("Failed to create essences layer from JSON")

    return layer

def configure_essence_field(
    layer,
    essence_field,
    essence_secondaire_field,
    essences,
    codes,
    with_variation=False
):
    """
    Configure primary/secondary essence widgets and constraint.

    Parameters
    ----------
    layer : QgsVectorLayer
    essence_field : str
        Field name for primary essence.
    essence_secondaire_field : str
        Field name for secondary essence.
    essences : QgsVectorLayer
        Layer containing species reference.
    codes : list[str]
        Codes allowed for primary essence.
    with_variation : bool
        Whether to include variation in labels.
    """

    fe = FieldEditor(layer)

    primary_map, secondary_map = _build_essence_maps(
        essences,
        codes,
        with_variation
    )

    # value maps
    fe.add_value_map(essence_field, {"map": primary_map})
    fe.add_value_map(essence_secondaire_field, {"map": secondary_map}, allow_null=True)

    _set_essence_constraint(
        fe,
        essence_field,
        essence_secondaire_field
    )

def _build_essence_maps(essences, codes, with_variation):

    primary_map = {}
    secondary_map = {}

    codes_set = set(codes)

    for ess in essences.getFeatures():

        code = ess["code"]
        variation = ess["variation"]
        fid = ess["fid"]

        # Skip unwanted variations
        if with_variation and variation in _SKIP_VARIATIONS:
            continue

        label, target = _build_label(
            ess,
            code,
            variation,
            codes_set,
            with_variation,
            primary_map,
            secondary_map
        )

        if label not in target:
            target[label] = fid

    return primary_map, secondary_map

def _build_label(
    ess,
    code,
    variation,
    codes_set,
    with_variation,
    primary_map,
    secondary_map
):

    if code in codes_set:

        label = code

        if with_variation and variation:
            label = f"{code} {variation}"

        return label, primary_map

    else:

        if with_variation:
            label = ess["essence_variation"]
        else:
            label = ess["essence"]

        return label, secondary_map

def _set_essence_constraint(fe, essence_field, essence_secondaire_field):

    expr = f"""
    ((COALESCE("{essence_field}", '') <> '') AND "{essence_secondaire_field}" IS NULL)
    OR
    ((COALESCE("{essence_field}", '') = '') AND "{essence_secondaire_field}" IS NOT NULL)
    """

    msg = "Veuillez sélectionner une valeur pour ESSENCE ou ESSENCE_SECONDAIRE (mais pas les deux)."

    fe.set_constraint_expression(
        essence_field,
        expr,
        msg,
        QgsFieldConstraints.ConstraintStrengthHard
    )