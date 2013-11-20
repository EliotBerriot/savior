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
    parser.add_argument("action", help="""What should savior do ? (save|clean|purge)\n
    save: save given datasets\n
    clean: remove old saves from given datasets\n
    purge: remove all saves from given dataset
    """,
    choices=['save', 'clean', 'purge']
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
def main():
    try:
        parse_command_line(sys.argv)
        # Do something with arguments.
    finally:
        logging.shutdown()
 
 
if __name__ == "__main__":
    sys.exit(main())