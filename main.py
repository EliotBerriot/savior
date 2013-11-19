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
from errors import ParseConfigError
class Savior(LoggerAware):
    """
        The main class of Savior project
    """

    def __init__(
            self, 
            datasets_to_save="all",
            force_save=False, 
            send_mail=True
        ):
            
        self.datasets_to_save=datasets_to_save
        self.send_mail  = send_mail # If True, an email will be send to admins when save process is done
        self.settings = None  
        self.hosts = None
        # Parse settings.ini
        self.settings = ConfigParser.ConfigParser()
        self.settings.read("settings.ini")
        # if force_save is set to True, days_between_saves option in settings
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
        elif type(self.datasets_to_save) == list:
            datasets_names=self.datasets_to_save
           
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
            if self.force_save or ds.need_save():
                saved = ds.save()
                if saved :
                    self.saved_datasets.append(ds)
                else: 
                    self.not_saved_datasets.append(ds)
        self.log("save process ended : {0} datasets have been saved".format(len(self.saved_datasets)))
        if self.send_mail:            
            self.mail()
     
    def clean(self):
        """
            Remove old saves
        """
        self.log("cleaning {0} datasets...".format(len(self.datasets)))
        self.cleaned_datasets = []
        for ds in self.datasets:
            ds.remove_old_saves()
            self.cleaned_datasets.append(ds)
        self.log("save process ended : {0} datasets have been cleaned".format(len(self.cleaned_datasets)))
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
        self.log("checking hosts...")
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
            
    def mail(self):
        """
            Send a mail to all admins
        """
        self.log("Sending mail to admins...")
        
        formated_stamp = self.stamp.strftime('%Y-%m-%d %Hh%M')
        mail_content=""
        mail_subject=""        
        
        if len(self.saved_datasets)>0 and len(self.not_saved_datasets)==0:
            mail_subject = "Savior : {0} successfully ended".format(formated_stamp)
            mail_content+= "Savior script has run correctly on {0}.\n".format(formated_stamp)
            mail_content+= "{0} datasets were saved :\n".format(len(self.saved_datasets))
            for ds in self.saved_datasets:
                mail_content+= "- {0}\n".format(ds.name)
            
        elif len(self.saved_datasets)>0 and len(self.not_saved_datasets)>0:
            mail_subject = "Savior : {0} ended with maybe some errors".format(formated_stamp)
            mail_content+= "Savior script has run on {0}.\n".format(formated_stamp)
            mail_content+= "{0} datasets on {1} have been saved :\n".format(len(self.saved_datasets),len(self.datasets))
            
            for ds in self.saved_datasets:
                mail_content+= "  - {0}\n".format(ds.name)

            mail_content+= "\nFor some reaseon, the following datasets HAVE NOT been saved :\n"            
            for ds in self.not_saved_datasets:
                mail_content+= "  - {0}\n".format(ds.name)
            
        else:
            mail_subject = "Autosave : {0} script has failed".format(formated_stamp)
            mail_content+= "Autosave script has run on {0}.\n".format(formated_stamp)
            mail_content+= "Autosave : {0} script has failed, no datasets have been saved.\n".format(formated_stamp)            
        #log part
        mail_content+= "For more informations, please read the following log :\n\n"
        os.chdir(self.root_path)
        log = open(self.log_file, 'r').read()
        mail_content+=log
        
        sender=self.settings.get("mail", "from")
        to=self.settings.get("mail", "admins").split(",")
        to=filter(None, to)
        smtp={}
        try:
            smtp['hostname'] =  self.settings.get("mail", "smtp_hostname")
        except:
            raise ParseConfigError("'smtp_hostname' setting is missing in settings.ini")
        try:
            smtp['port'] =  self.settings.get("mail", "smtp_port")
        except:
            smtp['port'] = None
         
        try:
            smtp['username'] =  self.settings.get("mail", "smtp_username")
            smtp['password'] =  self.settings.get("mail", "smtp_password")
        except:
            smtp['username'] =  None
            smtp['password'] =  None
            
        msg = MIMEText(mail_content)
        msg["Subject"]=mail_subject
        msg["From"]=sender
        msg["To"]=", ".join(to)
        try:
            if smtp['port']:
                s = smtplib.SMTP(smtp['hostname'], smtp['port'])
            else:
                s = smtplib.SMTP(smtp['hostname'])
        except Exception, e:
            self.log("can't connect to SMTP server [{0}] : {1}".format(smtp['hostname'], e), "error")
            return False
        if smtp['username']:
            try:
                if smtp['username']:
                    s.login(smtp['username'], smtp['password'])
            except Exception, e:
                self.log("can't log to SMTP server [{0}] using given credentials : {1}".format(smtp['hostname'], e), "error")
                return False
        try:
            s.sendmail(sender, to, msg.as_string())
            s.quit()
            self.log("Mail successfully send")
            return True
        except Exception, e:    
            self.log("Error during mail sending process via SMTP server [{0}] : {1}".format(smtp['hostname'], e), "error")
                
        
class Dataset(LoggerAware):
    def __init__(self,savior, path, config_file):
        self.savior = savior
        self.savior_options = dict(self.savior.settings.items('global'))
        self.config = config_file
        self.settings = ConfigParser.ConfigParser()
        config_path = path+"/"+self.config
        self.get_logger()
        
        if not os.path.exists(config_path):
            raise ParseConfigError("File {0} does not exist".format(config_path))
            return None
        try:
            self.settings.read(config_path)
            self.get_global_config()
            
        except Exception, e:
            raise ParseConfigError(str(e))
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
    
    def need_save(self):
        """
            Return True if save process is needed. 
        """
        days_between_saves = int(self.get_option(
            name="days_between_saves",
            )
        )
        
        self.log('checking for saves created in the last {0} day(s)'.format(days_between_saves))
        recent_saves = self.get_saves_by_date(days_between_saves)
            
        if len(recent_saves) == 0:
            self.log('no save have been found in the last {0} day(s), we need to create a new one'.format(days_between_saves))
            self.remove_old_saves()
            return True
        else:
            self.log('{0} saves are present for the last {1} day(s)'.format(len(recent_saves), days_between_saves))
        
        self.log("No need to create a new save")
        return False
    def save(self):
        self.log("beginning of save process...")
            
        self.current_save_directory = self.create_directory(self.save_directory+"/"+self.savior.stamp_str)
        for save in self.sections:            
            if not save == "global":                    
                self.log("saving [{0}]...".format( save))
                data_options = dict(self.settings.items(save))
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
    def get_saves_by_date(self, days, operation="greater_than"):
        """
            Return a list of saves for current dataset that are older (greater_than) 
            or younger (lesser_than) than days number
        """
        if operation not in ["lesser_than", "greater_than"]:
            raise Exception('Unknown operation "{0}"'.format(operation))
        saves_list = []
        now = datetime.now()                
        saves = self.get_all_saves()
        if len(saves) == 0: # check if directory is empty
            self.log("no saves found for current dataset")
            return []
        else:              
            limit = now - timedelta(days)
            for save in saves: 
                save_datetime = datetime.strptime(save, self.savior.stamp_setting)                
                if operation =="lesser_than": 
                    if save_datetime < limit:
                        
                        saves_list.append(save)
                    
                elif operation =="greater_than":
                    if save_datetime > limit:
                        saves_list.append(save)
                else:
                    pass
            return saves_list            
        
    
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
        self.remove_old_saves()
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
    
    def remove_old_saves(self):
        
        # check if min_saves_nuber is respected
        min_saves_number = days_between_saves = int(self.get_option(
            name="min_saves_number",
            )
        )
        existing_saves = self.get_all_saves()
        self.log('checking save number...')
        ok_for_delete = 0 # amount of saves that can be safely delete
        if len(existing_saves) <= min_saves_number:
            self.log('number of existing saves ({0}) is inferior or equal to minimum saves number ({1})'.format(min_saves_number, len(existing_saves)))
            ok_for_delete = 0          
        else:
            self.log("there are more saves than the minimum amount required (min: {0}, found: {1})".format(min_saves_number, len(existing_saves)))
            ok_for_delete = len(existing_saves) - min_saves_number
            self.log('{0} saves can be deleted'.format(ok_for_delete))
        
        time_to_live = int(self.get_option(
            name="time_to_live",
            )
        )
        
        self.log('checking for saves older than {0} day(s)'.format(time_to_live))
        old_saves = sorted(self.get_saves_by_date(time_to_live, "lesser_than"))
        for s in old_saves:
            print s
        if len(old_saves) > 0:
            self.log('found {0} saves older than {1} day(s)'.format(len(old_saves),time_to_live))
            for save in old_saves:
                if ok_for_delete > 0:
                    self.remove(save)
                    ok_for_delete -= 1
                else:
                    break
        else:
            self.log('no save have older than {0} day(s), has been found'.format(time_to_live))
         
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
 