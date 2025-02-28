from PyQt5.QtSql import QSqlDatabase, QSqlQuery

class DatabaseUtils:
    def __init__(self):
        self.db = QSqlDatabase.addDatabase('QPSQL')
        self.db.setHostName('c3l5o0rb2a6o4l.cluster-czz5s0kz4scl.eu-west-1.rds.amazonaws.com')
        self.db.setDatabaseName('dfmt7djs1uirmt')
        self.db.setUserName('ueo45oicvq7lh8')
        self.db.setPassword('p128a3e76b86b7246f203e2e8e51286f5790546134f0e6075ab0b82f4ae16412d')
        self.db.setPort(5432)

    def open_connection(self):
        if not self.db.open():
            print("Failed to connect to the database.")
            return False
        return True

    def close_connection(self):
        if self.db.isOpen():
            self.db.close()

    def fetch_essence_map(self):
        # Implementation of fetch_essence_map
        pass
