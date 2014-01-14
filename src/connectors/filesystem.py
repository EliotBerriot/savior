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

from base import BaseConnector, SaveError, ConnectionError
import os

class FileSystemConnector(BaseConnector):
    """
        A connector designed to save folders and files on local
        machine
    """
    exclude = [] # excluded files or directories 
    
    
    def set_exclude(self, exclude):
        self.exclude = exclude
     
    def prepare_save(self):
        super(FileSystemConnector, self).prepare_save()
        self.path_to_save = self.data_options['path']
        self.exclude = self.data_options.get('exclude', "").split(",")
        self.set_logger_message_prefix('Filesystem [{0}] - '.format(self.dataset_name))
        
    def check_connection(self):
        self.prepare_save()
        try:          
            os.access(self.path_to_save, os.F_OK)
            os.access(self.path_to_save, os.R_OK)
            self.log("Savior has read access to directory {0}".format(self.path_to_save))
            return True
        except Exception, e:            
            raise ConnectionError("Savior can't read directory {0}".format(self.path_to_save))
            return False
    def get_save_path(self):
        return self.save_path+"/"+self.name+".tar.gz"
        
    def prepare_connection(self):
        super(FileSystemConnector, self).prepare_connection()
        
    def save(self):
        super(FileSystemConnector, self).save()
        exclude_param= " "        
        for x in self.exclude:
            if len(x)>0:
                exclude_param+='--exclude="{0}" '.format(x)            
    
            command = 'tar -pczf "{0}" {1} "{2}"'.format(
                self.get_save_path(),
                exclude_param, 
                self.path_to_save
                )
            self.log("running {0}".format(command))
            l = self.run(command)
            
            if l != 0:
                raise SaveError("Can't run the following command : {0}. Check path name ({1}) and permissions.".format(command, self.path_to_save))
                return False
            else:
                self.log("[{0}] files have been tared".format(
                    self.name,
                    )
                )
                return True
