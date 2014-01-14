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

from utils import LoggerAware

class SaviorError(LoggerAware, Exception):
    def __init__(self, message):
        self.set_message(message)
        self.get_logger()
        self.log(self.message, "critical")
        
    def set_message(self, message):
        self.message = message
        
    def __str__(self):
        return self.message
        
class ParseConfigError(SaviorError):
    
    def set_message(self, message):
        self.message = """Error while parsing config file : {0}""".format(message)

class CheckConfigError(SaviorError):
    def set_message(self, message):
        self.message = """Savior has met a critical error while checking configuration files and connection to hosts: {0}. Please double-check your hosts.ini and settings.ini files.""".format(message) 
