from base import DatabaseConnector, SaveError, ConnectionError
from fabric.api import local, hide, settings


class MySQLConnector(DatabaseConnector):
    """
        A connector designed to save MySQL databases
    """    
     
    def prepare_connection(self):
        super(MySQLConnector, self).prepare_connection()
        self.set_logger_message_prefix('MySQL [{0}] - '.format(self.host['hostname']))
        
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
                self.log("database [{0}] has been dumped".format(
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
                    "can't connect to database '{1}'".format(self.database)
                    )
                return False
            else:
                self.log("connection OK")
                return True