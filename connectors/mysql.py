from base import DatabaseConnector, SaveError, ConnectionError
from fabric.api import local, hide, settings
import logging

logger = logging.getLogger('autosave')

class MySQLConnector(DatabaseConnector):
    """
        A connector designed to save MySQL databases
    """    
        
    def save(self):
        super(MySQLConnector, self).save()
        with hide('running'):
            l = local(
                "mysqldump -u {0} --password={1} {2} > {3}/{4}.sql".format(
                    self.credentials["username"],
                    self.credentials["password"],                    
                    self.database,
                    self.save_path,
                    self.name
                )
            )

            if l.return_code == 2:
                raise SaveError(self.dataset_name, l)
            else:
                logger.info("{0}/{1} database has been saved".format(
                    self.dataset_name,
                    self.name,
                    )
                )
                
    def check_connection(self):
        super(MySQLConnector, self).check_connection()
        with hide('running'):            
            l = local(
                'mysql -u {0} --password={1} -e "exit"'.format(
                    self.credentials["username"], 
                    self.credentials["password"])
            )
            if l.return_code == 2:
                raise ConnectionError(
                    "Can't connect to MySQL database '{1}'".format(self.database)
                    )
                return False
            else:
                logger.info("Connection to MySQL database OK")
                return True