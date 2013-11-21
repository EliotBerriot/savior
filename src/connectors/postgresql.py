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


class PostgreSQLConnector(DatabaseConnector):
    """
        A connector designed to save MySQL databases
    """    
     
    default_port = 5432
    def prepare_connection(self):
        super(PostgreSQLConnector, self).prepare_connection()
        self.set_logger_message_prefix('PostgreSQL [{0}] - '.format(self.host['hostname']))
       
    def set_password(self, password):
        self.run('export PGPASSWORD="{0}"'.format(password))
    def save(self):
        super(PostgreSQLConnector, self).save()
        self.set_password(self.credentials["password"])
        command = """pg_dump -U "{0}" -h "{1}" -p {2} "{3}" > "{4}/{5}.sql" """.format(
                self.credentials["username"],  
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
        super(PostgreSQLConnector, self).check_connection()    
        self.set_password(self.credentials["password"])
        command = """psql -U "{0}" -h "{1}" -p {2} -c \\\q""".format(
                self.credentials["username"],  
                self.host['hostname'],
                self.host['port'],
            )
            
        l = self.run(command)
        if l != 0:
            raise ConnectionError(
                "can't connect to database server '{0}'".format(self.host['hostname'])
                )
            return False
        else:
            self.log("connection OK")
            return True