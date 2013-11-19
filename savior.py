 # -*- coding: utf-8 -*-

import os, sys
import ConfigParser
from datetime import datetime, timedelta
from fabric.api import local, hide, settings
import shutil
import smtplib
from email.mime.text import MIMEText
from connectors import mapping
from utils import LoggerAware

class Savior(LoggerAware):
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
        # Parse settings.ini
        self.settings = ConfigParser.ConfigParser()
        self.settings.read("settings.ini")
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
        self.stamp_setting = self.settings.get("global", "folder_name")
        self.stamp_str =  self.stamp.strftime(self.stamp_setting)
        self.log_setup()
        
        
        self.check_config()
        
        # path to the current script
        self.root_path = os.path.dirname(os.path.realpath(__file__))
        os.chdir(self.root_path)

        # path to datasets saves
        settings_save_path = self.settings.get("global","save_path")
        if not settings_save_path[0] == "/":
            # if save path in settings file is relative
            self.save_path = self.root_path+"/"+settings_save_path
        else:
            self.save_path = settings_save_path
        
        self.saved_datasets = []
        self.not_saved_datasets = []
        self.last_save_too_recent_datasets = []
        
        # create datasets
        self.datasets_path = self.root_path+"/datasets" 
        self.datasets = []
        datasets_names = []
        [f for f in os.listdir('.') if os.path.isfile(f)]
        #get name of datasets to save
        if self.datasets_to_save=="all":
            os.chdir(self.datasets_path)
            datasets_names = [f for f in os.listdir("./") if os.path.isfile(f)]
            os.chdir(self.root_path)
        # save a single dataset
        else:
            datasets_names.append(self.datasets_to_save)
           
        # instantiate datasets objects
        for file_name in datasets_names:            
            ds = Dataset(self, self.datasets_path, file_name)
            self.datasets.append(ds)
            
    def log_setup(self):
        # create file handler which logs even debug messages
        self.log_file = 'logs/{0}.log'.format(
            self.stamp_str
            )
        self.init_logger()
 
    def save(self):
        self.log("saving {0} datasets...".format(len(self.datasets)))
        self.saved_datasets = []
        for ds in self.datasets:
            saved = ds.save()
            if saved :
                self.saved_datasets.append(ds)
        self.log("save process ended : {0} datasets have been saved".format(len(self.saved_datasets)))
        
     
    def purge(self):
        self.log("purging {0} datasets...".format(len(self.datasets)))
        for ds in self.datasets:
            ds.purge()
        self.log("purge process ended".format(len(self.saved_datasets)))
        
    def check_config(self):
        """
            Check if settings and hosts.ini are correctly written, 
            check credentials and hosts access
        """
    
        # Parse hosts.ini
        self.hosts = {}
        with open(os.path.join(os.getcwd(),'hosts.ini'),'r') as configfile: 
            hosts = ConfigParser.ConfigParser()
            hosts.readfp(configfile)
        # check connexion for each host, if needed
        
        for host in hosts.sections():
            options = dict(hosts.items(host))
            self.hosts[host] = options
            # get connector instance from type setting
            connector = mapping.MAPPING[options["type"]](host_options=options)
            connector.check_connection()
class Dataset(LoggerAware):
    def __init__(self,savior, path, config_file):
        self.savior = savior
        self.savior_options = dict(self.savior.settings.items('global'))
        self.config = config_file
        self.settings = ConfigParser.ConfigParser()
        config_path = path+"/"+self.config
        self.get_logger()
        
        if not os.path.exists(config_path):
            raise ParseConfigError(self.config, "File does not exist")
            return None
        try:
            self.settings.read(config_path)
            self.get_global_config()
            
        except Exception, e:
            raise ParseConfigError(self.config, str(e))
            return None
        self.sections = self.settings.sections()            
        self.name = config_file  
        self.set_logger_message_prefix('Dataset [{0}] - '.format(self.name))
        self.save_directory = self.create_directory(self.savior.save_path+"/"+self.name)
    def get_global_config(self):
        """
            get settings for global section of dataset files
        """
        self.global_options = dict(self.settings.items("global"))
        self.global_settings= {}
        self.global_settings['time_to_live'] = self.get_option('time_to_live')
        self.global_settings['days_between_saves'] = self.get_option('days_between_saves')
        self.global_settings['ftp_backup'] = self.get_option('ftp_backup')
     
    def save(self):
        self.log("beginning of save process...")
        days_between_saves = int(self.get_option(
            name="days_between_saves",
            )
        )
        if not self.check_delay_between_saves(days_between_saves):
            self.log("last save is recent enough, no need to create a new one")
            return False
        else:
            self.current_save_directory = self.create_directory(self.save_directory+"/"+self.savior.stamp_str)
            for save in self.sections:            
                if not save == "global":                    
                    self.log("saving [{0}]...".format( save))
                    data_options = dict(self.settings.items(save))
                    
                    
                    self.log("last save is too old, creating a new one")
                
                    kwargs = {
                        "dataset_name": self.name,
                        "name":save,
                        "save_path":self.current_save_directory,
                        "dataset_save_id":self.savior.stamp_str,
                        }
                        
                    if data_options.get("host", None):
                        host_options = self.savior.hosts[data_options["host"]]
                    else:
                        host_options= {}
                    connector = mapping.MAPPING[data_options["type"]](
                        data_options = data_options,
                        dataset_options=self.global_options,
                        savior_options=self.savior_options, 
                        host_options=host_options,
                        **kwargs 
                        )
                    connector.save()
                    self.log("[{0}] successfully saved".format(save))
            if self.post_save():
                self.log("save process successfully ended")
                return True
            else:
                return False           
      
    def check_delay_between_saves(self, days):
        now = datetime.now()
        try:        
            saves = self.get_all_saves()
            s = saves[0] # check if directory is empty
        except Exception, e:
            self.log("no saves found for current dataset")
            return True
        else:            
            most_recent_save = () # [name, datetime]
            for save in saves:          
                save_datetime = datetime.strptime(save, self.savior.stamp_setting)
                if len(most_recent_save) == 0:
                    most_recent_save = (save, save_datetime)
                else:
                    if save_datetime > most_recent_save[1]:
                        most_recent_save = (save, save_datetime)
            limit = now - timedelta(days)
            if most_recent_save[1] < limit  :
                return True
            else:
                return False
                
    def post_save(self):
         
        """
            Called when dataset save process (tar, dumps, etc.) is done
        """
        ftp_backup = self.get_option('ftp_backup', []).split(',')
        for host in ftp_backup:
            host_options = self.savior.hosts[host]
            kwargs = {
                "dataset_name": self.name,
                "local_saves_directory":self.savior.save_path, 
                "dataset_save_id":self.savior.stamp_str, 
                }
            connector = mapping.MAPPING['ftpupload'](
                    host_options=host_options,
                    **kwargs 
                    )
            connector.upload()  
        return True
           
    def get_option(self, name, default=None):
        """
            Look for option in  global_options
            If not found, look in savior_options
            else : return default value
        """
        if self.global_options.get(name, None):
            return self.global_options[name]
        elif self.savior_options.get(name, None):   
            return self.savior_options[name]
        else:
            return default      
            
    def create_directory(self, directory): 
        if not os.path.exists(directory):
            os.mkdir(directory)
        return directory
    def purge(self):
        """
            Remove all saves for this dataset
        """
        self.log("purging dataset...")
        shutil.rmtree(self.save_directory)
        ftp_backup = self.get_option('ftp_backup', []).split(',')
        for host in ftp_backup:
            host_options = self.savior.hosts[host]
            kwargs = {
                "dataset_name": self.name,
                "local_saves_directory":self.savior.save_path, 
                }
            connector = mapping.MAPPING['ftpupload'](
                    host_options=host_options,
                    **kwargs 
                    )
            
            connector.purge() 
        self.log("dataset have been purged")
    def remove(self, dataset_save_id):
        """
            remove a given save from saves folder and from hosts
        """
        self.log("removing save [{0}]...".format(dataset_save_id))
        shutil.rmtree(self.save_directory+'/'+dataset_save_id)
        ftp_backup = self.get_option('ftp_backup', []).split(',')
        for host in ftp_backup:
            host_options = self.savior.hosts[host]
            kwargs = {
                "dataset_name": self.name,
                "local_saves_directory":self.savior.save_path, 
                "dataset_save_id":self.savior.stamp_str, 
                }
            connector = mapping.MAPPING['ftpupload'](
                    host_options=host_options,
                    **kwargs 
                    )
            connector.remove()            
        self.log("save [{0}] has been removed...".format(dataset_save_id))
        
    def get_all_saves(self):
        """
            return a list of all saves for current dataset
        """
        saves = os.walk(self.save_directory).next()[1]
        return saves
        

    
class ParseConfigError(Exception):
    def __init__(self, name, e):
        self.message = """{0} : Error while parsing config file. Error : {1}""".format(name, e)
        logger.critical(self.message)
    def __str__(self):
        return self.message