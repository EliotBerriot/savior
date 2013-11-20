from base import RemoteConnector, SaveError, ConnectionError
from fabric.api import local, hide, settings
import paramiko
import ftplib
import sys, os

class FTPUploadConnector(RemoteConnector):
    """
        A connector designed to backup files to FTP server
    """
    remote_saves_directory="" 
    local_saves_directory=""
    session=None
    sftp = False
    sftp_port = 22
    ftp_port = 21
    def get_default_port(self):
        if self.sftp:
            return self.sftp_port
        else:
            return self.ftp_port
    def set_remote_saves_directory(self, remote_saves_directory):
        self.remote_saves_directory = remote_saves_directory
        
    def set_local_saves_directory(self, local_saves_directory):
        self.local_saves_directory = local_saves_directory
    
    def prepare_connection(self):
        super(FTPUploadConnector, self).prepare_connection()
        self.local_saves_directory = self.kwargs.get('local_saves_directory', None)
        self.remote_saves_directory = self.get_host_option('save_path', './')
        self.sftp = self.convert_to_boolean(self.get_host_option('sftp', False))
        self.set_logger_message_prefix('FTP Host [{0}] - '.format(self.host['hostname']))
    def check_connection(self):       
        super(FTPUploadConnector, self).check_connection()
        try:            
            self.connect()
            self.close_connection()
            self.log("connection OK")
            return True
        except Exception, e:            
            raise ConnectionError(str(e))
            return False
    def connect(self):         
        self.prepare_connection()
        hostname = self.host["hostname"]
        port = self.host["port"]
        username = self.credentials["username"]
        password = self.credentials["password"]
        if self.sftp:
            transport = paramiko.Transport((hostname, port))
            transport.connect(username = username, password = password)
            self.session = paramiko.SFTPClient.from_transport(transport)
        else:
            self.session = ftplib.FTP(
                hostname,
                username,
                password,
            )
        self.init_connection()
     
    def close_connection(self):
        if self.sftp:
            self.session.close()
        else:
            self.session.quit()
    def init_connection(self):
        self.chdir(self.remote_saves_directory)
    def get_connection(self):
        """
            Get FTP session or create it
        """
        if not self.session:
            self.connect()
        self.chdir(self.remote_saves_directory)
        
    def upload(self):
        self.prepare_save()
        self.get_connection()
        #self.session.cwd(self.get_or_create(self.remote_saves_directory))
        os.chdir(self.local_saves_directory)
        
        # check if dataset directory already exists on remote host
        #self.session.cwd(self.get_or_create(self.dataset_name))
        self.get_or_create(self.dataset_name)
        os.chdir(self.dataset_name)
        # check if current save directory already exists on remote host
        os.chdir(self.dataset_save_id)
        self.log("uploading files...")
        self.upload_directory(os.getcwd())
        self.close_connection()
        
     
    def chdir(self, path):
        if self.sftp:
            self.session.chdir(path)
        else:
            self.session.cwd(path)
    def get_or_create(self, dir): 
        """
            from http://stackoverflow.com/questions/10644608/create-missing-directories-in-ftplib-storbinary
        """
        if self.directory_exists(dir) is False: # (or negate, whatever you prefer for readability)
            self.mkdir(dir)
        self.chdir(dir)
    
    def directory_exists(self, dir):
        
        filelist = self.listdir() 
        current = self.getcwd()
        try:
            self.chdir(dir)
            self.chdir(current)
        except Exception:
            return False
        """
        for f in filelist:
            if f.split()[-1] == dir and f.upper().startswith('D'):
                return True
        return False
        """
        
    def upload_directory(self, directory): 
        """
            recursively upload local directory on FTP host
        """
        
        self.get_or_create(directory.split('/')[-1])
        
        for root, dirs, files in os.walk(directory):
            os.chdir(directory)
            for file in files:
                self.upload_file(file)                
            for dir in dirs:
                self.upload_directory(dir)
        os.chdir("../")
        self.chdir("../")
        return directory
        
    def upload_file(self, file_name):
        if self.sftp:
            self.session.put(file_name, self.getcwd()+"/"+file_name)
        else:
            file = open(file_name, "rb")
            self.session.storbinary("STOR " + file_name, file)   
            file.close()
      
    def delete(self):
        """
            Delete a save from FTP host
        """
        self.connect()
        remote_path = "/".join(
            self.remote_saves_directory,
            self.dataset_name,
            self.dataset_save_id
        )
        # remote_path looks like /var/www/mysavesfolder/myblog/11-09-2013  
        try:
            self.delete_directory(remote_path)
            self.log(
                "{0} directory removed server".format(remote_path)
                )
        except Exception, e:
            self.log("can't remove {0} from server".format(remote_path), "warning")

    def is_file(self, name):
        """
            Check if the given FTP item is a file or a directory
        """
        current = self.getcwd()
        try:
            self.chdir(name)
        except:
            self.chdir(current)
            return True
        self.chdir(current)
        return False

    def getcwd(self):
        if self.sftp:
            return self.session.getcwd()
        else :            
            return self.session.pwd()
            
    def mkdir(self, name, path="."):
        if self.sftp:
            return self.session.mkdir(path+"/"+name)
        else :            
            return self.session.mkd(name) 
    def rmdir(self, name):
        if self.sftp:
            return self.session.rmdir(name)
        else :            
            return self.session.rmd(name)
    def delete_file(self, name):
        if self.sftp:
            return self.session.remove(name)
        else :            
            return self.session.delete(name)
        
    def listdir(self, name="./"):
        if self.sftp:
            return self.session.listdir(name)
        else :            
            return self.session.nlst(name)
            
    def delete_directory(self, path="./"):
         
        try:
            self.log(
                "removing {0}...".format(self.getcwd()+"/"+path)
                )
            self.chdir(path) 
            names = self.listdir()
            for name in names:
                if self.is_file( name):
                    self.delete_file(name)
                else:
                    directory = name
                    self.delete_directory(directory)

            self.chdir("../")
            self.rmdir(path)
        except Exception, e:
            self.log(
                "can't remove {0} : path does not exist or permission denied".format(self.getcwd()+"/"+path, "warning")
                )
    
    def purge(self):
        """
            Remove all saves of a dataset from a given host
        """
        self.prepare_save()
        self.get_connection() 
        self.delete_directory(self.dataset_name)
        
    def remove(self):
        """
            Remove a save from FTP host
        """
        self.prepare_save()
        self.get_connection()
        try:
            self.chdir(self.dataset_name)
        except Exception, e:
            self.log(
                "{0} : path does not exist or permission denied".format(self.getcwd()+"/"+self.dataset_name)
                )
        else:
            self.delete_directory(self.dataset_save_id)
        
class FTPUploadError(SaveError):
    pass