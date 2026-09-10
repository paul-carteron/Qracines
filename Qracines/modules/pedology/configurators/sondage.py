from ....core.layer import FieldEditor


class SondageConfigurator:
    def __init__(self, layer, stations):
        self.fields = FieldEditor(layer)
        self.stations = stations

    def configure(self):
        self.fields.add_value_map(
            "station",
            {"map": [{str(station): str(station)} for station in self.stations]},
        )
