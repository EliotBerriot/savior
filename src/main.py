# -*- coding: utf-8 -*-
# Copyright (C) 2013 Eliot Berriot <contact@eliotberriot.com>
#
# This file is part of savior.
#
# Savior is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Savior is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Savior.  If not, see <http://www.gnu.org/licenses/>.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.
import os, sys, traceback
import ConfigParser
from datetime import datetime, timedelta
import shutil
import smtplib
from email.mime.text import MIMEText
from connectors import mapping
from utils import LoggerAware, ConfigAware
from errors import ParseConfigError
from dataset import Dataset
class Savior(LoggerAware, ConfigAware):
    """
        The main class of Savior project
    """

    def __init__(
            self, 
            datasets_to_save="all",
            force_save=False, 
            send_mail=True
        ):
          
        
        # path to savior folder
        self.datasets_to_save=datasets_to_save
        self.send_mail  = send_mail # If True, an email will be send to admins when save process is done
        self.settings = None  
        self.hosts = None
        self.datasets = []
        # if force_save is set to True, days_between_saves option in settings
        # will be ignored
        
        self.force_save = force_save

        self.load_settings() 
        self.log_setup()
        
    def load_datasets(self):
        if self.datasets: # datasets have already been loaded
            return self.datasets
        else:
            self.check_config()
            
            self.saved_datasets = []
            self.not_saved_datasets = []
            self.dont_need_save_datasets = []
            
            # create datasets
            self.datasets_path = self.root_path+"/datasets" 
            
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
                
            return self.datasets
        
    def log_setup(self):
        # create file handler which logs even debug messages
        self.log_file = self.root_path+'/logs/{0}.log'.format(
            self.stamp_str
            )
        self.init_logger()
 
    def save(self):
        self.load_datasets()
        
        self.log("Save id [{0}]".format(self.stamp_str))
        self.log("Saving {0} datasets...".format(len(self.datasets)))
        self.saved_datasets = []
        exception=False
        for ds in self.datasets:
            if not exception :
                if (self.force_save or ds.need_save()):
                    try:
                        saved = ds.save()
                        self.saved_datasets.append(ds)
                            
                    except Exception, e:                        
                        self.log(traceback.format_exc())
                        exception = True
                        self.not_saved_datasets.append(ds)
                        self.log("Save process has met a critical error: {0}".format(e), "critical")
                        self.log("Skipping save for all remaining datasets")
                        ds.remove()
                else:
                    self.dont_need_save_datasets.append(ds)
            else:
                self.not_saved_datasets.append(ds)
        self.log("Save process ended : {0} datasets have been saved".format(len(self.saved_datasets)))
        if self.send_mail:            
            self.mail()
     
    def clean(self):
        """
            Remove old saves
        """
        self.load_datasets()
        self.log("cleaning {0} datasets...".format(len(self.datasets)))
        self.cleaned_datasets = []
        for ds in self.datasets:
            ds.remove_old_saves()
            self.cleaned_datasets.append(ds)
        self.log("save process ended : {0} datasets have been cleaned".format(len(self.cleaned_datasets)))
    def purge(self):
        self.load_datasets()
        self.log("purging {0} datasets...".format(len(self.datasets)))
        for ds in self.datasets:
            ds.purge()
        self.log("purge process ended".format(len(self.saved_datasets)))
        
    def check(self):
        self.check_config()
        
    def load_settings(self):
        
        self.root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))        
        os.chdir(self.root_path)
        
        # Parse settings.ini
        settings = os.path.join(self.root_path, 'settings.ini')
        self.settings = ConfigParser.ConfigParser()
        config = self.settings.read(settings)
        if len(config) == 0:
            raise ParseConfigError("Can't open {0} : ensure file exists or is readable".format(settings))
        
        # stamp used for logs and directory names
        self.stamp = datetime.now()
        self.stamp_setting = self.settings.get("global", "folder_name")
        self.stamp_str =  self.stamp.strftime(self.stamp_setting)
        
        # path to datasets saves
        settings_save_path = self.settings.get("global","save_path")
        if not settings_save_path[0] == "/":
            # if save path in settings file is relative
            self.save_path = self.root_path+"/"+settings_save_path
        else:
            self.save_path = settings_save_path
            
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
        
        if len(self.saved_datasets)+ len(self.dont_need_save_datasets)==len(self.datasets) and len(self.not_saved_datasets)==0:
            mail_subject = "Savior : {0} successfully ended".format(formated_stamp)
            mail_content+= "Savior script has run correctly on {0}.\n".format(formated_stamp)
            mail_content+= "{0} datasets were saved :\n".format(len(self.saved_datasets))
            for ds in self.saved_datasets:
                mail_content+= "- {0}\n".format(ds.name)
                
            mail_content+= "{0} datasets did not need save :\n".format(len(self.dont_need_save_datasets))
            for ds in self.dont_need_save_datasets:
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
            mail_subject = "Savior : {0} script has failed".format(formated_stamp)
            mail_content+= "Savior script has run on {0}.\n".format(formated_stamp)
            mail_content+= "Savior : {0} script has failed, no datasets have been saved.\n".format(formated_stamp)            
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
             
    
