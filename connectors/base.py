class BaseConnector(object):
    """
        A connector is designed to save a particular type of     
        data (email, database, local filesystem...)
    """
    dataset_name = ""
    dataset_save_id = ""
    path = ""  # local path were saves are temprarily stored
    
    def set_dataset_name(self, dataset_name):
        self.dataset_name = dataset_name
        
    def set_dataset_save_id(self, dataset_save_id):
        self.dataset_save_id = dataset_save_id
    
    def set_path(self, path):
        self.path = path
        
    def save(self):
        pass
    
    def check_connection(self):
        """
            Check if the connector is working properly using given
            informations
        """
        return True

class CredentialsConnector(BaseConnector):
    """
        A connector dedicated to save process that needs credentials
        (username and password), like database or FTP
    """
    credentials = {}
    def set_credentials(self, credentials):
        self.credentials = credentials

class RemoteConnector(CredentialsConnector):
    """
        A connector dedicated to save process that involve a remote
        host
    """
    host = {}
    def set_host(self, host):
        self.host = host
class DatabaseConnector(RemoteConnector):
    """
        A connector dedicated to save process that involve a remote
        host
    """
    database=""
    def set_database(self, database):
        self.database = database # a database name

class SaveError(Exception):
    def __init__(self, name, e):
        self.message = """{0} : Error while saving. Autosave is cancelling. Error
            : {1}""".format(name, e)
        logger.critical(self.message)
    def __str__(self):
        return self.message

class ConnectionError(Exception):
    def __init__(self, message):
        self.message = message
        logger.critical(self.message)
    def __str__(self):
        return self.message