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

import logging
import subprocess
from ..utils import LoggerAware, ConfigAware
from ..errors import SaviorError
class BaseConnector(LoggerAware, ConfigAware):
    """
        A connector is designed to save a particular type of     
        data (email, database, local filesystem...)
    """
    name = ""
    dataset_save_id = ""
    save_path = ""  # local path were saves are temprarily stored
    
    def __init__(self, 
            data_options={}, 
            dataset_options={}, 
            savior_options={},
            host_options={},
            **kwargs):
        self.data_options = data_options
        self.dataset_options = dataset_options 
        self.savior_options = savior_options
        self.host_options = host_options
        self.kwargs = kwargs
        self.get_logger()
        
    def get_dataset_option(self, name, default=None):
        """
            Look for option in  dataset_options
            If not found, look in savior_options
            else : return default value
        """
        if self.dataset_options.get(name, None):
            return self.dataset_options[name]
        elif self.savior_options.get(name, None):   
            return self.savior_options[name]
        else:
            return default
    
    def get_host_option(self, name, default=None):
        """
            Look for option in  data_options
            If not found, look in hosts_options
            else : return default value
        """
        if self.data_options.get(name, None):
            return self.data_options[name]
        elif self.host_options.get(name, None):  
            return self.host_options[name]
        else:
            return default
    def set_name(self, name):
        self.name = name
        
    def set_dataset_save_id(self, dataset_save_id):
        self.dataset_save_id = dataset_save_id    
        
    def prepare_save(self):
        self.prepare_connection()
        #self.dataset_save_id = self.data_options["dataset_save_id"]        
        self.name = self.kwargs.get('name', None)
        self.dataset_name = self.kwargs.get('dataset_name')
        self.set_logger_message_prefix('Dataset [{0}] - '.format(self.dataset_name))
        self.save_path = self.kwargs.get('save_path', None)
        self.dataset_save_id = self.kwargs.get('dataset_save_id')
        
    def save(self):
        self.prepare_save()
    
    def prepare_connection(self):
        pass
    def check_connection(self):
        """
            Check if the connector is working properly using given
            informations
        """        
        self.prepare_connection()
        self.log("checking...")
        return True

    def run(self, command):
        """
            run subprocess.call
        """
        devnull = open('/dev/null', 'w') # hide output        
        process = subprocess.call(command, shell=True)#, stdout=devnull, stderr=devnull)
        return process
class CredentialsConnector(BaseConnector):
    """
        A connector dedicated to save process that needs credentials
        (username and password), like database or FTP
    """
    credentials = {}
    def set_credentials(self):
        self.credentials['username'] = self.get_host_option('username')
        self.credentials['password'] = self.get_host_option('password')
    def prepare_connection(self):
        super(CredentialsConnector, self).prepare_connection()
        self.set_credentials()
        
class RemoteConnector(CredentialsConnector):
    """
        A connector dedicated to save process that involve a remote
        host
    """
    host = {}
    default_port = 0
    def set_host(self):
        self.host['hostname'] = self.get_host_option('hostname')       
        self.host['port'] = int(self.get_host_option('port', self.get_default_port()))
        
    def prepare_connection(self):
        super(RemoteConnector, self).prepare_connection()
        self.set_host()
        
    def get_default_port(self):
        return self.default_port
        
class DatabaseConnector(RemoteConnector):
    """
        A connector dedicated to save process that involve a database
    """
    database=""
    def prepare_connection(self):
        super(DatabaseConnector, self).prepare_connection()
        self.database = self.data_options.get('database', None)

class SaveError(SaviorError):
    def set_message(self, message):
        self.message = """Error while saving : {0}""".format(message)

class ConnectionError(SaviorError):
    def set_message(self, message):
        self.message = """Error while connecting : {0}""".format(message)