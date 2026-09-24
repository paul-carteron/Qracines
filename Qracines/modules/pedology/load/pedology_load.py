from pathlib import Path

from Qracines.utils.message import messageLog
from Qracines.utils.variable import get_global_variable, get_project_variable

from ....utils.config import get_guides, get_qfield_path, get_stations
from ....utils.layers import create_relation, load_gpkg
from ....utils.utils import fold, unfold
from ..configurators.horizons import HorizonsConfigurator
from ..configurators.sondage import SondageConfigurator

from qgis.core import QgsMapLayer


class PedologyLoad:
    def __init__(self):
        self.gpkg_path = get_qfield_path("pedology")

    @staticmethod
    def _get_guide(layer):
        if layer.fields().indexFromName("GUIDE") == -1:
            raise RuntimeError(
                "Le champ GUIDE est absent du géopackage. "
                "Recréez le projet pédologique avec la version actuelle."
            )

        known_guides = set(get_guides())
        guides = set()
        for feature in layer.getFeatures():
            value = feature["GUIDE"]
            if value is None:
                continue
            value = str(value).strip()
            if value and value != "NULL":
                if value not in known_guides:
                    raise RuntimeError(f"Guide pédologique inconnu : {value}")
                guides.add(value)

        if not guides:
            raise RuntimeError("Aucun guide n'est renseigné dans la couche sondage.")
        if len(guides) > 1:
            raise RuntimeError(
                "Plusieurs guides sont présents dans la couche sondage : "
                + ", ".join(sorted(guides))
            )

        return guides.pop()

    def load(self):
        layers = load_gpkg(self.gpkg_path, group_name="PEDOLOGY")

        missing = {"sondage", "horizons", "sondage_horizons"}.difference(layers)
        if missing:
            raise RuntimeError("Couches manquantes dans le géopackage : "+ ", ".join(sorted(missing)))

        guide = self._get_guide(layers["sondage"])
        try:
            stations = get_stations(guide)
        except KeyError as exc:
            raise RuntimeError(f"Guide pédologique inconnu : {guide}") from exc

        relation = create_relation(layers["sondage"], layers["horizons"], "UUID", "SONDAGE")
        SondageConfigurator(layers["sondage"],stations,relation=relation,guide=guide,).configure()
        HorizonsConfigurator(layers["horizons"]).configure()

        # --- Apply internal styles if available
        style_directory = get_global_variable("QS2_styles_directory")
        style_name = "PEDO_sondage_horizons.qml"

        if layers["sondage_horizons"] and style_directory:
            styles = list(Path(style_directory).rglob(style_name))

            if styles:
                msg, ok = layers["sondage_horizons"].loadNamedStyle(str(styles[0]), QgsMapLayer.AllStyleCategories)
                messageLog(f"[STYLE] {msg}")

                if ok:
                    self.update_categories(layers["sondage_horizons"])
                else:
                    messageLog(f"[STYLE] Failed to load {styles[0]}", level="e")
            else:
                messageLog(f"[STYLE] Missing {style_name}", level="w")

        fold()
        unfold("PEDOLOGY")

        return layers

