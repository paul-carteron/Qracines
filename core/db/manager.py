from qgis.core import QgsDataSourceUri, QgsVectorLayer, QgsFeatureRequest

import os
import json
from ...utils.config import get_config_path

class DatabaseManager:
    def __init__(self):
        config_path = get_config_path("db.json")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Database config not found at {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        self.host = config.get("db_host")
        self.port = config.get("db_port")
        self.database = config.get("db_database")
        self.username = config.get("db_username")
        self.password = config.get("db_password")

    def load_layer_from_query(self, sql_query, layer_name, geometry_column=None):
        """
        Load a SQL query result as a layer in QGIS.

        Args:
            query (str): The raw SQL query (without _uid_ wrapping).
            layer_name (str): The name of the layer in QGIS.
            geometry_column (str): The name of the geometry column (None for non-geometry).
        """
        # Build the query with _uid_
        sql_query = f"({sql_query})"

        # Create the URI
        uri = QgsDataSourceUri()
        uri.setConnection(self.host, self.port, self.database, self.username, self.password)
        uri.setDataSource("", sql_query, geometry_column, "", "fid")

        # Create the layer
        layer = QgsVectorLayer(uri.uri(), layer_name, "postgres")

        return layer
    
    @staticmethod
    def q_essences():
        query = """
        SELECT 
            ev.id as fid,
            e.name AS essence,
            concat_ws(' ', e.name, ev.variation) AS essence_variation,
            e.code,
            ev.variation,
            ev.ordre,
            e.type
        FROM public.gestion_essencevariation AS ev
        JOIN public.gestion_essence AS e ON ev.essence_id = e.id
        ORDER BY ev.ordre ASC
        """
        return query
    
    def load_essences(self, name = "essences"):
        layer = self.load_layer_from_query(sql_query=self.q_essences(), layer_name = name)

        if not layer or not layer.isValid():
            raise RuntimeError("Failed to load or validate the essences layer")

        # Materialize all features (use `setNoAttributes()` if you only want geometries)
        request = QgsFeatureRequest().setFilterFids(layer.allFeatureIds())
        materialized_layer = layer.materialize(request)

        if not materialized_layer or not materialized_layer.isValid():
            raise RuntimeError("Failed to materialize the essences layer")

        return materialized_layer

