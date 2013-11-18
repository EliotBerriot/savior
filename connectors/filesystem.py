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
     
    def prepare_save(self):
        super(FileSystemConnector, self).prepare_save()
        self.path_to_save = self.data_options['path']
        self.exclude = self.data_options.get('exclude', "").split(",")
        
    def get_save_path(self):
        return self.save_path+"/"+self.name
        
    def save(self):
        super(FileSystemConnector, self).save()
        exclude_param= " "        
        for x in self.exclude:
            exclude_param+='--exclude="{0}" '.format(x)
            
        with settings(warn_only=True):
            l = local('tar -cf "{0}.tar" {1} "{2}"'.format(
                self.get_save_path(),
                exclude_param, 
                self.path_to_save
                )
            )
            if l.return_code == 2:
                raise SaveError(self.name, l)
                return False
            else:
                logger.info("{0}/{1} files have been tared".format(
                    self.dataset_name,
                    self.name,
                    )
                )
                return True
