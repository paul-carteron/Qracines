from qgis.core import QgsFieldConstraints
from ..core.layer.manager import FieldEditor


_SKIP_VARIATIONS = {"foudroyé", "nécrosé", "dépérissant"}

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