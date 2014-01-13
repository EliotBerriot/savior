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

from base import DatabaseConnector, SaveError, ConnectionError

class MySQLConnector(DatabaseConnector):
    """
        A connector designed to save MySQL databases
    """    
     
    default_port = 3306
    def prepare_connection(self):
        super(MySQLConnector, self).prepare_connection()
        self.set_logger_message_prefix('MySQL [{0}] - '.format(self.host['hostname']))
        
    def save(self):
        super(MySQLConnector, self).save()
        command = """mysqldump -u "{0}" --password='{1}' -h "{2}" --port {3} --databases "{4}" > "{5}/{6}.sql" """.format(
                self.credentials["username"],
                self.credentials["password"],  
                self.host['hostname'],
                self.host['port'],
                self.database,
                self.save_path,
                self.name
            )
            
        l = self.run(command)

        if l != 0:
            raise SaveError(l)
        else:
            self.log("database [{0}] has been dumped".format(
                self.name,
                )
            )
                
    def check_connection(self):
        super(MySQLConnector, self).check_connection()                
        command = """mysql -u "{0}" --password='{1}' -h "{2}" --port {3} -e "exit" """.format(
                self.credentials["username"],
                self.credentials["password"],  
                self.host['hostname'],
                self.host['port'],
                self.database,
            )
            
        l = self.run(command)
        if l != 0:
            raise ConnectionError(
                "can't connect to database server '{0}'".format(self.host['hostname'])
                )
            return False
        else:
            self.log("Successfully connected on port {0} as user {1}, on database {2}".format(self.host["port"], self.credentials["username"], self.database))
            
            return True