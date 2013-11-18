from base import RemoteConnector, SaveError, ConnectionError
from fabric.api import local, hide, settings
import paramiko
import ftplib
import logging
import sys, os
logger = logging.getLogger('autosave')

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
        self.sftp = self.get_host_option('sftp', False)
    def check_connection(self):       
        super(FTPUploadConnector, self).check_connection()
        try:            
            self.connect()
            self.close_connection()
            logger.info("{0} : FTP connection OK".format(self.host['hostname']))
            return True
        except Exception, e:
            
            message = """Can't connect to FTP server using given credentials. Error : {0}""".format(str(e))
            raise ConnectionError(message)
            return False
    def connect(self): 
        hostname = self.host["hostname"]
        port = self.host["port"]
        username = self.credentials["username"]
        password = self.credentials["password"]
        self.prepare_connection()
        if self.sftp:
            transport = paramiko.Transport((hostname, port))
            transport.connect(username = username, password = password)
            self.session = paramiko.SFTPClient.from_transport(transport)
        else:
            print('standard ftp')
            self.session = paramiko.FTPClient.from_transport(transport)
        self.init_connection()
     
    def close_connection(self):
        self.session.close()
    def init_connection(self):
        self.session.chdir(self.remote_saves_directory)
    def get_connection(self):
        """
            Get FTP session or create it
        """
        if not self.session:
            self.connect()
        self.session.chdir(self.remote_saves_directory)
        
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
        try:
            os.chdir(self.dataset_save_id)
            logger.info("Uploading files...")
            self.upload_directory(os.getcwd())
            self.session.close_connection()
        except Exception, e:
            raise FTPUploadError(e)
     
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
            self.session.mkd(dir)
        self.session.chdir(dir)
    
    def directory_exists(self, dir):
        
        filelist = []
        self.session.retrlines('LIST',filelist.append)
        for f in filelist:
            if f.split()[-1] == dir and f.upper().startswith('D'):
                return True
        return False
        
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
            logger.info(
                "{} directory removed from FTP server.".format(remote_path)
                )
        except Exception, e:
            logger.debug("Can't remove {0} from FTP server".format(remote_path))

    def is_file(self, name):
        """
            Check if the given FTP item is a file or a directory
        """
        current = session.pwd()
        try:
            self.chdir(name)
        except:
            self.chdir(current)
            return True
        self.chdir(current)
        return False

    def delete_directory(self, path):
        
        directory = path.split("/")[-1]
        self.chdir(path)       
        names = self.nlst(path)
        for name in names:
            if self.is_file( name):
                self.session.delete(name)
            else:
                self.delete_directory(path+"/"+directory)

        self.chdir("../")
        self.session.rmd(directory)
    
        
class FTPUploadError(SaveError):
    pass
    