from ....utils.config import get_guides, get_qfield_path, get_stations, get_style
from ....utils.layers import create_relation, load_gpkg
from ....utils.message import messageLog
from ....utils.utils import fold, unfold
from ....utils.variable import get_global_variable
from ..configurators.sondage import SondageConfigurator


class PedologyLoad:
    def __init__(self):
        self.gpkg_path = get_qfield_path("pedology")

    @staticmethod
    def _all_stations():
        return list(
            dict.fromkeys(
                station
                for guide in get_guides()
                for station in get_stations(guide)
            )
        )

    def load(self):
        layers = load_gpkg(self.gpkg_path, group_name="PEDOLOGY")

        missing = {"sondage", "horizons"}.difference(layers)
        if missing:
            raise RuntimeError(
                "Couches manquantes dans le géopackage : "
                + ", ".join(sorted(missing))
            )

        self._apply_styles(layers)
        self._create_relation(layers)
        SondageConfigurator(
            layers["sondage"], self._all_stations()
        ).configure()

        fold()
        unfold("PEDOLOGY")

        return layers

    @staticmethod
    def _create_relation(layers):
        return create_relation(
            layers["sondage"],
            layers["horizons"],
            "uuid",
            "sondage",
            relation_id="sondage_horizons",
            relation_name="sondage",
        )

    @staticmethod
    def _apply_styles(layers):
        style_dir = get_global_variable("QS2_styles_directory") or None

        for name, layer in layers.items():
            try:
                style_path = get_style(name, styles_dir=style_dir)
                error_message, loaded = layer.loadNamedStyle(str(style_path))
                if not loaded:
                    messageLog(f"Could not style layer {name}: {error_message}")
                layer.triggerRepaint()
            except Exception as exc:
                messageLog(f"Could not style layer {name}: {exc}")
