from ....utils.config import get_guides, get_qfield_path, get_stations
from ....utils.layers import create_relation, load_gpkg
from ....utils.utils import fold, unfold
from ..configurators.horizons import HorizonsConfigurator
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

        relation = self._create_relation(layers)
        SondageConfigurator(
            layers["sondage"], self._all_stations(), relation=relation
        ).configure()
        HorizonsConfigurator(layers["horizons"]).configure()

        fold()
        unfold("PEDOLOGY")

        return layers

    @staticmethod
    def _create_relation(layers):
        return create_relation(
            layers["sondage"],
            layers["horizons"],
            "UUID",
            "SONDAGE",
            relation_id="sondage_horizons",
            relation_name="sondage",
        )
