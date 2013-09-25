from base import RemoteConnector, SaveError, ConnectionError
from fabric.api import local, hide, settings
import ftplib
import logging

logger = logging.getLogger('autosave')

class FTPConnector(RemoteConnector):
    """
        A connector designed to save FTP files or to backup files to FTP server
    """
    remote_saves_directory="" 
    local_saves_directory=""
    session=None
    
    def set_remote_saves_directory(self, remote_saves_directory):
        self.remote_saves_directory = remote_saves_directory
    
    def set_local_saves_directory(self, local_saves_directory):
        self.local_saves_directory = local_saves_directory
    
    def check_connection(self):        
        try:            
            self.connect()
            self.session.quit()
            logger.info("FTP connection OK")
            return True
        except Exception, e:
            message = "Can't connect to FTP server using given
credentials. Error : {0}".format(str(e))
            raise ConnectionError(message)
            return False
     def connect(self):        
        self.session = ftplib.FTP(
                self.host["hostname"],
                self.credentials["username"],
                self.credentials["password"],
            )
        self.init_connection()
        
    def get_connection(self):
        """
            Get FTP session or create it
        """
        if not self.session:
            self.connect()
        self.session.cwd(self.remote_saves_directory)
        
    def upload(self):
        self.get_connection()
        os.chdir(self.local_saves_directory)
        
        # check if dataset directory already exists on remote host
        self.session.cwd(self.get_or_create(self.dataset_name))
        
        # check if current save directory already exists on remote host
        try:
            self.session.mkd(self.dataset_save_id)
            self.session.cwd(self.dataset_save_id)            
            logger.info("Uploading files...")
            self.upload_directory(os.getcwd())
            self.session.quit()
        except Exception, e:
            raise FTPUploadError(e)
                
    def get_or_create(self, directory_name):
        """
            check if given directory exists on remote host, create it
            if it doesn't
        """
        filelist = self.session.nlst(self.session.pwd()) 
        exists=False
        i = 0
        for f in filelist:
            if directory_name == f.split("/")[-1]:
                exists = True
            i+=1
        if not exists:
            self.session.mkd(directory_name)
        return directory_name
        
    def upload_directory(self, directory): 
    """
        recursively upload local directory on FTP host
    """
        print(directory)
        self.session.mkd(directory)
        self.session.cwd(directory)
        for root, dirs, files in os.walk(directory):
            os.chdir(directory)
            for file in files:
                self.upload_file(file)                
            for dir in dirs:
                self.upload_directory(dir)
        os.chdir("../")
        self.session.cwd("../")
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
            self.session.cwd(name)
        except:
            self.session.cwd(current)
            return True
        self.session.cwd(current)
        return False

    def delete_directory(self, path):
        
        directory = path.split("/")[-1]
        self.session.cwd(path)       
        names = self.session.nlst(path)
        for name in names:
            if self.is_file( name):
                self.session.delete(name)
            else:
                self.delete_directory(path+"/"+directory)

        self.session.cwd("../")
        self.session.rmd(directory)
    
    def disconnect(self):
        self.session.quit()
        
class FTPUploadError(SaveError):
    pass
    