# used to mapp type settings in datasets files to a connector class
from filesystem import FileSystemConnector
from mysql import MySQLConnector
from ftp import FTPUploadConnector

MAPPING = {
    "ftpupload": FTPUploadConnector,
    #"ftpdownload": FTPDownloadConnector,
    "filesystem": FileSystemConnector,
    "mysql": MySQLConnector,
    }
