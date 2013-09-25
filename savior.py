 # -*- coding: utf-8 -*-

import os
import ConfigParser
from datetime import datetime, timedelta
from fabric.api import local, hide, settings
import ftplib
import shutil
import smtplib
from email.mime.text import MIMEText
import logging
import connectors.filesystem import FileSystemConnector
import connectors.mysql import MySQLConnector
import connectors.ftp import FTPConnector

logger = logging.getLogger('autosave')
logger.setLevel(logging.DEBUG)

class Savior(object):
    """
        The main class of Savior project
    """

    def __init__(
            self, 
            datasets_to_save="all",
            force_save=False, 
        ):
            
        self.datasets_to_save=datasets_to_save
        
        self.settings = None  
        self.hosts = None
        
        self.get_config()
        # if force_safe is set to True, days_between_saves option in settings
        # will be ignored
        self.force_save = force_save

        # enable filesystem saving
        #self.save_filesystem = save_filesystem

        # enable databases dump
        # self.save_databases = save_databases
        # enable ftp backup
        # self.ftp_backup = ftp_backup
        
        # stamp used for logs and directory names
        self.stamp = datetime.now()
        
        self.log=None
        self.log_setup()        
        
        # path to the current script
        self.root_path = os.path.dirname(os.path.realpath(__file__))
        os.chdir(self.root_path)

        # path to datasets saves
        settings_save_path = self.settings.get("save","save_path")
        if not settings_save_path[0] == "/":
            # if save path in settings file is relative
            self.save_path = self.root_path+"/"+settings_save_path
        else:
            self.save_path = settings_save_path
        
        self.saved_datasets = []
        self.not_saved_datasets = []
        self.last_save_too_recent_datasets = []
        # create datasets objects
        self.datasets_path = self.root_path+"/datasets" 
        self.datasets = []
        if self.datasets_to_save=="all":
            for file in list(self.files(self.datasets_path)):           
                # exclude files ending with a ~
                if (file[-1]!="~"):             
                    ds = Dataset(self, self.datasets_path, file)
                    self.datasets.append(ds)
        # save a single dataset
        else:
            try:
                ds = Dataset(self.datasets_path, self.datasets_to_save)
                self.datasets.append(ds)
            except Exception, e:
                pass
    def log_setup(self):
        # create file handler which logs even debug messages
        self.log = 'logs/{0}.log'.format(
            self.stamp.strftime(self.settings.get("global", "folder_name"))
            )
        fh = logging.FileHandler(self.log)
        fh.setLevel(logging.DEBUG)
        
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        
        # create formatter and add it to the handlers
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
            )
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)
        # add the handlers to logger
        logger.addHandler(ch)
        logger.addHandler(fh)
 
    def save(self):
        for ds in self.datasets:
        
    def get_config(self):
        """
            Check if settings and hosts.ini are correctly written, 
            check credentials and hosts access
        """
        
        # Parse settings.ini
        self.settings = ConfigParser.ConfigParser()
        self.settings.read("settings.ini")
    
        # Parse settings.ini
        self.hosts = ConfigParser.ConfigParser()
        self.hosts.read("hosts.ini")
        
        # check if ftp_backup settings correspond to a real host in host files
        if self.settings.has_option("save","ftp_backup"):
            ftp_backup = self.settings.get("save","ftp_backup").split(",")
            for h in ftp_backup:
                try:
                    credentials = {
                        "username":self.hosts.get(h,"username"),
                        "password":self.hosts.get(h,"password"),
                    }
                    host = {   
                        "username":self.hosts.get(h,"hostname"),
                    }
                    if self.hosts.has_option(h, "port"):
                        host["port"] = self.hosts.get(h, "port")
                    
                    ftp_connector = FTPConnector()
                    ftp_connector.set_credentials(credentials)
                    ftp_connector.set_host(host)
                                    
                    ftp_connector.check_connection()
                except Exception, e:
                    logger.critical(e)
                    
        #
        
class Dataset():
    def __init__(self, path, config_file):
        self.config = config_file
        self.settings = ConfigParser.ConfigParser()
        config_path = path+"/"+self.config
        if not os.path.exists(config_path):
            raise ParseConfigError(self.config, "File does not exist")
            return None
        try:
            self.settings.read(config_path)
        except Exception, e:
            raise ConfigParseError(self.config, str(e))
            return None
        self.sections = self.settings.sections()
        self.name = config_file        
        
            
class ParseConfigError(Exception):
    def __init__(self, name, e):
        self.message = "{0} : Error while parsing config file. Error :
{1}".format(name, e)
        logger.critical(self.message)
    def __str__(self):
        return self.message