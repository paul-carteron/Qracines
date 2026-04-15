from qgis.core import (
    QgsVectorLayer,
    QgsFields,
    QgsField,
    QgsCoordinateReferenceSystem,
)


class LayerFactory:
    """Factory for creating in-memory vector layers from schema definitions."""

    DEFAULT_CRS = "EPSG:2154"

    @classmethod
    def create(cls, name: str, schema: dict, crs: str | None = None):
        """
        Create a memory layer from a schema.

        Parameters
        ----------
        name : str
            Layer name
        schema : dict
            Schema definition with keys:
                - fields
                - geometry (optional)
        crs : str, optional
            CRS auth id (default EPSG:2154)

        Returns
        -------
        QgsVectorLayer
        """

        fields = schema.get("fields", [])
        geometry = schema.get("geometry")

        return cls.create_memory_layer(
            layer_name=name,
            fields_list=fields,
            geometry=geometry,
            crs=crs or cls.DEFAULT_CRS,
        )

    @classmethod
    def create_all(cls, schemas: dict):
        return {
            name: cls.create(name, schema)
            for name, schema in schemas.items()
        }

    @staticmethod
    def create_memory_layer(layer_name, fields_list, geometry=None, crs="EPSG:2154"):   
        """Low level layer creation."""

        # geometry definition
        if geometry:
            crs_obj = QgsCoordinateReferenceSystem(crs)
            geometry_str = f"{geometry}?crs={crs_obj.authid()}"
        else:
            geometry_str = "None"

        layer = QgsVectorLayer(geometry_str, layer_name, "memory")

        if not layer.isValid():
            raise RuntimeError(f"Failed to create memory layer '{layer_name}'")

        # add fields
        fields = QgsFields()
        for field_name, field_type in fields_list:
            fields.append(QgsField(field_name, field_type))

        layer.dataProvider().addAttributes(fields)
        layer.updateFields()

        return layer