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


import sys
import argparse
import logging
from src.main import Savior

import sys
sys.path.append(".")

logger = logging.getLogger('savior')
logger.setLevel(logging.DEBUG)
def parse_command_line(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("action", help="""What should savior do ?\n
    save: save given datasets\n
    clean: remove old saves from given datasets\n
    purge: remove all saves from given dataset
    check: check your configuration files for syntax errors, and try to connect to every host in hosts.ini\n
    """,
    choices=['save', 'clean', 'purge', 'check']
    )
    parser.add_argument('-nm', '--no-mail',action='store_false', help="Won't send any mail")
    
    parser.add_argument('-ds', '--datasets', nargs='+', type=str, help="A list of datasets concerned by the command", required=False)
    parser.add_argument("-f","--force-save",action='store_true', help="Force save (does not check for delay between saves)")
    args = parser.parse_args()
    
    send_mail = True
    if args.no_mail != None:
        send_mail = args.no_mail
    datasets = None
    if args.datasets:
        datasets = args.datasets
    else:
        datasets = 'all'
    s = Savior(
        datasets_to_save = datasets,
        force_save = args.force_save,
        send_mail = send_mail
    )
    
    if args.action =="save":
        s.save()
    if args.action =="clean":
        s.clean()
    if args.action =="purge":
        s.purge()
    if args.action =="check":
        s.check_config()
def main():
    try:
        parse_command_line(sys.argv)
        # Do something with arguments.
    finally:
        logging.shutdown()
 
 
if __name__ == "__main__":
    sys.exit(main())