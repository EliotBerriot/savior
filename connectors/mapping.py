# used to mapp type settings in datasets files to a connector class
from connectors.filesystem import FileSystemConnector
from connectors.mysql import MySQLConnector
from connectors.ftp import FTPConnector

MAPPING = {
    "ftp": FTPConnector,
    "filesystem": FileSystemConnector,
    "mysql": MySQLConnector,
    }
