from base import BaseConnector, SaveError
from fabric.api import local, hide, settings
import logging
import os

logger = logging.getLogger('autosave')

class FileSystemConnector(BaseConnector):
    """
        A connector designed to save folders and files on local
        machine
    """
    exclude = [] # excluded files or directories 
    
    
    def set_exclude(self, exclude):
        self.exclude = exclude
        
    def save(self):
        exclude_param= " "        
        for x in self.exclude:
            exclude_param+='--exclude="{0}" '.format(x)
            
        with settings(warn_only=True):
            l = local('tar -cf "{0}.tar" {1} "{2}"'.format(
                self.name,
                exclude_param, 
                self.path
                )
            )
            if l.return_code == 2:
                raise SaveError(self.name, l)
                return False
            else:
                return True
