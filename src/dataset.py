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

import os, sys
import ConfigParser
from datetime import datetime, timedelta
import shutil
import smtplib
from email.mime.text import MIMEText
from connectors import mapping
from utils import LoggerAware, ConfigAware, folder_size, human_size
from errors import ParseConfigError

class Dataset(LoggerAware, ConfigAware):
    def __init__(self,savior, path, config_file):
        self.savior = savior
        self.savior_options = dict(self.savior.settings.items('global'))
        self.get_logger()
        self.config = config_file
        self.settings = ConfigParser.ConfigParser()
        config_path = path+"/"+self.config
        self.size = 0 #the size of save
        
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
    
    def check_config(self):

        self.check_connection()

    def get_config(self, save):
        data_options = dict(self.settings.items(save))
        kwargs = {
            "dataset_name": self.name,
            "name":save,
            "save_path":self.get_current_directory_name(),
            "dataset_save_id":self.savior.stamp_str,
            }
            
        if data_options.get("host", None):
            host_options = self.savior.hosts[data_options["host"]]
        else:
            host_options= {}

        return (kwargs, data_options, host_options)

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
            self.log('no save has been found in the last {0} day(s), we need to create a new one'.format(days_between_saves))
            return True
        else:
            self.log('{0} saves are present for the last {1} day(s)'.format(len(recent_saves), days_between_saves))
        
        self.log("No need to create a new save")
        return False

    def get_connector(self, save):
        kwargs, data_options, host_options = self.get_config(save)
        connector = mapping.MAPPING[data_options["type"]](
            data_options = data_options,
            dataset_options=self.global_options,
            savior_options=self.savior_options, 
            host_options=host_options,
            **kwargs 
            )
        return connector
    def check_connection(self):
        self.log("Checking connections...")
        for save in self.sections:            
            if not save == "global":  
                self.get_connector(save).check_connection()

    def get_current_directory_name(self):
        return self.save_directory+"/"+self.savior.stamp_str

    def save(self):
        self.log("beginning of save process...")
            
        self.current_save_directory = self.create_directory(self.get_current_directory_name())
        for save in self.sections:            
            if not save == "global":                    
                self.log("saving [{0}]...".format( save))
                
                self.get_connector(save).save()
                self.log("[{0}] successfully saved".format(save))
        if self.post_save():
            self.log("save  {0})".format(self.current_save_directory))
            
            self.log("save process successfully ended (total size: {0})".format(human_size(self.size)))
            
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
        keep_local_saves = self.convert_to_boolean(self.get_option('keep_local_saves'))
        self.size += folder_size(self.current_save_directory, human=False)
        if not keep_local_saves:
            self.remove_local_save()
        self.remove_old_saves()
        return True
    
    def remove_local_save(self):
        """
            Clean current save local directory (but leave the directory itself)
        """
        self.log("Cleaning local save folder...")
        for the_file in os.listdir(self.current_save_directory):
            file_path = os.path.join(self.current_save_directory, the_file)
            try:
                os.unlink(file_path)
            except Exception, e:
                print e
                
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
        self.log('remove old saves...')
        ok_for_delete = 0 # amount of saves that can be safely delete
        if len(existing_saves) <= min_saves_number:
            self.log('number of existing saves ({0}) is inferior or equal to minimum saves number ({1})'.format(len(existing_saves),min_saves_number))
            ok_for_delete = 0  
            return 
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
        
        self.log("Saves too old: {0}".format(old_saves.join(", ")))
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
        self.log("dataset has been purged")
    def remove(self, dataset_save_id=None):
        """
            remove a given save from saves folder and from hosts
        """
        if not dataset_save_id: # if not specified, remove current save
            dataset_save_id = self.savior.stamp_str
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
 