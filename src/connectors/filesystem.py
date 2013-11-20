from base import BaseConnector, SaveError
from fabric.api import local, hide, settings
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
        
    def get_save_path(self):
        return self.save_path+"/"+self.name
        
    def save(self):
        super(FileSystemConnector, self).save()
        exclude_param= " "        
        for x in self.exclude:
            exclude_param+='--exclude="{0}" '.format(x)
            
        with hide('everything'):
            with settings(warn_only=True):
                command = 'tar -cf "{0}.tar" {1} "{2}"'.format(
                    self.get_save_path(),
                    exclude_param, 
                    self.path_to_save
                    )
                self.log("running {0}".format(command)
                l = local(command)
                if l.return_code == 2:
                    raise SaveError("Can't run the following command : {0}. Check path name ({1}) and options.".format(command, self.path_to_save))
                    return False
                else:
                    self.log("[{0}] files have been tared".format(
                        self.name,
                        )
                    )
                    return True
