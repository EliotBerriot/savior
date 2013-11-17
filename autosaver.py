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

logger = logging.getLogger('autosave')
logger.setLevel(logging.DEBUG)


class Autosaver():
    def __init__(self, datasets_to_save="all",force_save=False, save_filesystem = True, save_databases = True, ftp_backup = True):
        self.root_path = os.path.dirname(os.path.realpath(__file__))
        os.chdir(self.root_path)
        self.datasets_to_save = datasets_to_save
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
                ds = Dataset(self, self.datasets_path, self.datasets_to_save)
                self.datasets.append(ds)
            except Exception, e:
                pass
        
    def save(self):

        # check if credential provided in settings.ini are working
        try: 
            self.check_credentials()
        except SaveError:
            return None
                    
        logger.debug("Starting autosave : {0}\n================================".format(self.stamp.strftime(self.settings.get("global", "folder_name"))))
        current_dataset = None
        try:
            for dataset in self.datasets:
                dataset.save()
                current_dataset = dataset
                logger.debug("Dataset : {0}\n------------------".format(dataset.name))
                
                dataset.saver.save() 
                
        except SaveError, e:
            current_dataset.saver.clear_save() # delete the current save
        self.mail()
        logger.debug("\n================================\nAutosave ended : {0}".format(datetime.now().strftime('%Y-%m-%d %Hh%M')))
        
    # return all files under a directory (but not recursively)
    def files(self, path): 
        for file in os.listdir(path):
            if os.path.isfile(path+"/"+file):
                yield file        
    
    
    def mail(self):
        formated_stamp = self.stamp.strftime('%Y-%m-%d %Hh%M')
        mail_content=""
        mail_subject=""        
        
        if len(self.saved_datasets)>0 and len(self.not_saved_datasets)==0:
            mail_subject = "Autosave : {0} successfully ended".format(formated_stamp)
            mail_content+= "Autosave script has run correctly on {0}.\n".format(formated_stamp)
            mail_content+= "{0} datasets were saved :\n".format(len(self.saved_datasets))
            for ds in self.saved_datasets:
                mail_content+= "- {0}\n".format(ds.name)
            
        elif len(self.saved_datasets)>0 and len(self.not_saved_datasets)>0:
            mail_subject = "Autosave : {0} ended with some errors".format(formated_stamp)
            mail_content+= "Autosave script has run on {0}.\n".format(formated_stamp)
            mail_content+= "{0} datasets on {1} have been saved :\n".format(len(self.saved_datasets),len(self.saved_datasets)+len(self.not_saved_datasets))
            
            for ds in self.saved_datasets:
                mail_content+= "  - {0}\n".format(ds.name)

            mail_content+= "\nBecause of an error during the save process, the following datasets HAVE NOT been saved :\n"            
            for ds in self.not_saved_datasets:
                mail_content+= "  - {0}\n".format(ds.name)
            
        else:
            mail_subject = "Autosave : {0} script has failed".format(formated_stamp)
            mail_content+= "Autosave script has run on {0}.\n".format(formated_stamp)
            mail_content+= "Autosave : {0} script has failed, no datasets have been saved.\n".format(formated_stamp)            
        #log part
        mail_content+= "For more informations, please read the following log :\n\n"
        os.chdir(self.root_path)
        log = open(self.log, 'r').read()
        mail_content+=log

        print(mail_content)
        
        sender=self.settings.get("mail", "from")
        to=self.settings.get("mail", "admins").split(",")
        to=filter(None, to)
        smtp=self.settings.get("mail", "smtp")

        msg = MIMEText(mail_content)
        msg["Subject"]=mail_subject
        msg["From"]=sender
        msg["To"]=", ".join(to)
        try:
            s = smtplib.SMTP(smtp)
            s.sendmail(sender, to, msg.as_string())
            s.quit()

        except Exception, e:
            logger.critical("Error while sending message : {0}".format(str(e)))
    # remove dataset saves that are too old, regarding their time to live
    def clean(self):
        for ds in self.datasets:
            ds.saver.clean()
    def purge(self):
        for ds in self.datasets:
            ds.saver.purge()
class Dataset():
    def __init__(self, parent, path, config_file):
        self.parent = parent        
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
        self.save_directory = self.parent.save_path+"/"+self.name
        self.saver=Saver(self, self.parent.operations) 
        
        
    # create the save directory for the dataset
    def create_save_directory(self): 
        if not os.path.exists(self.save_directory):
            os.mkdir(self.save_directory)
        return self.save_directory
    
    def save(self):
        
        try:            
            self.save_directory = self.create_save_directory()            
            logger.debug("'{0}' config file successfully parsed".format(self.name))
            
        except Exception,e:
            logger.critical("Dataset {0} has syntax error in dataset file. Autosave aborted.".format(self.config))
            
            return None

class Saver():
    def __init__(self, dataset, operations):
        self.dataset = dataset
        self.operations = operations        
        self.stamp = self.dataset.parent.stamp
        self.save_path = dataset.save_directory
        # create the timestamped save directory, under the dataset save directory
        self.save_directory = ""
        self.ftp_dataset_directory =""
        self.ftp_save_directory =""
        self.ftp_saved=False
        self.filesystem_saved=False
        self.mysql_saved=False
    def check_delay_between_saves(self):
        now = datetime.now()
        dbs = 0 # day_between_saves, in days
        # import custom dataset days_between_saves, if it exist in the dataset config file
        if self.dataset.settings.has_option("global", "days_between_saves"):
            dbs = int(self.dataset.settings.get("global", "days_between_saves"))
        # use the default days_between_saves (in settings.ini)
        else :
            dbs = int(self.dataset.parent.settings.get("global", "days_between_saves"))
        try:      
            saves = os.walk(self.save_path).next()[1]
            s = saves[0]
        except Exception, e:
            logger.warning("There are no saves under {0}".format(self.save_path))
            return True
        else:
            
            most_recent_save = [] # [name, datetime]
            for save in saves:            
                save_datetime = datetime.strptime(save, self.dataset.parent.settings.get("global", "folder_name"))
                if len(most_recent_save) == 0:
                    most_recent_save = [save, save_datetime]
                else:
                    if save_datetime > most_recent_save[1]:
                        most_recent_save = [save, save_datetime]
            limit = now - timedelta(dbs)
            if most_recent_save[1] < limit  :
                logger.info("{0}/{1} : last save is too old, creating a new one.".format(save, self.dataset.name))
                return True
            else:
                logger.info("{0}/{1} : last save is recent enough, no need to create a new one.".format(save, self.dataset.name))
                self.dataset.parent.last_save_too_recent_datasets.append(self.dataset)
                return False
    def save(self):        

        # check if delay between saves is respected
        if not self.dataset.parent.force_save:
            delay_is_okay = self.check_delay_between_saves()
            if not delay_is_okay:
                return 0
        self.save_directory = self.create_save_directory()
        os.chdir(self.save_directory)

        for section in self.dataset.sections:
            if section != "global":
                save_type = self.dataset.settings.get(section, "type")
                if save_type == "filesystem" and self.operations['filesystem']:
                    self.dump_filesystem(section)

                if save_type == "mysql" and self.operations['mysql']:                        
                    self.dump_mysql(section)            
            
        if self.operations['ftp']: 
            self.ftp_backup()
        self.dataset.parent.saved_datasets.append(self.dataset)
        self.clean() # clean old saves after saving new ones

    # create a folder inside a dataset save directory, using a timestamp
    def create_save_directory(self):
        stamp =  self.stamp.strftime(self.dataset.parent.settings.get("global", "folder_name"))
        dir = self.save_path+"/"+stamp
        os.mkdir(dir)
        return dir

    def clear_save(self, save="current"):
        if save == "current":
            self.dataset.parent.not_saved_datasets.append(self.dataset)    
            
        else: 
            self.save_directory = self.save_path+"/"+save
            self.mysql_saved = True
            self.filesystem_saved = True
            self.ftp_saved = True
        
        if self.filesystem_saved or self.mysql_saved:        
            self.filesystem_clear_save()
        if self.ftp_saved:
            self.ftp_clear_save()    

        logger.info("{0}/{1} has been removed".format(self.dataset.name, self.save_directory))
        

    # put the save on the FTP server
    
            
    

    
    
    def filesystem_clear_save(self):
        shutil.rmtree(self.save_directory)
        logger.info("{0}/{1} directory deleted from local filesystem.".format(self.dataset.name, self.save_directory.split("/")[-1]))
    
    def clean(self):
        now = datetime.now()
        ttl = 0 # time to live, in days
        # import custom dataset time to live, if it exist in the dataset config file
        if self.dataset.settings.has_option("global", "time_to_live"):
            ttl = int(self.dataset.settings.get("global", "time_to_live"))
        # use the default time to live (in settings.ini)
        else :
            ttl = int(self.dataset.parent.settings.get("global", "time_to_live"))
        try:        
            saves = os.walk(self.save_path).next()[1]            
        except:
            logger.warning("There are no saves under {0}".format(self.save_path))
        else:
            for save in saves:            
                save_datetime = datetime.strptime(save, self.dataset.parent.settings.get("global", "folder_name"))
                limit = now - timedelta(ttl)
                if save_datetime < limit  :
                    logger.info("{0}/{1} is older than {2} days".format(save, self.dataset.name, ttl))
                    self.clear_save(save)
    def purge(self):
        try:        
            saves = os.walk(self.save_path).next()[1]
        except:
            logger.warning("There are no saves under {0}".format(self.save_path))
        else:
            for save in saves:            
                self.clear_save(save)
class ParseConfigError(Exception):
    def __init__(self, name, e):
        self.message = "{0} : Error while parsing config file. Error : {1}".format(name, e)
        logger.critical(self.message)
    def __str__(self):
        return self.message
