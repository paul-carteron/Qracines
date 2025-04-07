from qgis.core import QgsDataSourceUri, QgsVectorLayer

import os
import json

class DatabaseManager:
    def __init__(self, config_path=None):
        config_path = os.path.join(os.path.dirname(__file__), '..', 'db.json')
        self.load_config(config_path)

    def load_config(self, config_path):
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
            # Assign values from the JSON file to class attributes
            self.host = config.get("db_host")
            self.port = config.get("db_port")
            self.database = config.get("db_database")
            self.username = config.get("db_username")
            self.password = config.get("db_password")
        else:
            raise FileNotFoundError(f"Config file not found at {config_path}")

    def load_layer_from_query(self, sql_query, layer_name, geometry_column=None):
        """
        Load a SQL query result as a layer in QGIS.

        Args:
            query (str): The raw SQL query (without _uid_ wrapping).
            layer_name (str): The name of the layer in QGIS.
            geometry_column (str): The name of the geometry column (None for non-geometry).
        """
        # Build the query with _uid_
        sql_query = f"(SELECT row_number() over () AS _uid_,* FROM ({sql_query}) AS _subq_1_ )"

        # Create the URI
        uri = QgsDataSourceUri()
        uri.setConnection(self.host, self.port, self.database, self.username, self.password)
        uri.setDataSource("", sql_query, geometry_column, "", "_uid_")

        # Create the layer
        layer = QgsVectorLayer(uri.uri(), layer_name, "postgres")

        return layer
    
    @staticmethod
    def q_essences():
        query = """SELECT e.name AS essence, concat_ws(' ', e.name, ev.variation) AS essence_variation, e.code, ev.variation, ev.ordre, e.type
        FROM public.gestion_essencevariation AS ev
        JOIN public.gestion_essence AS e
        ON ev.essence_id = e.id
        WHERE concat_ws(' ', e.name, ev.variation) NOT LIKE '%sain%'
        ORDER BY ev.ordre ASC
        """
        return query
  
    def load_essences(self):
        return self.load_layer_from_query(sql_query = self.q_essences(), layer_name = "essences")
