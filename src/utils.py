
import logging
import sys, os
class LoggerAware(object):
    """
        This class provide facilities to log messages
    """
    logger_name = "savior"
    logger = None
    logger_message_prefix = "" # a prefix for all logged messages
    logger_message_prefix_set = False # if this prefix has already been set
    def init_logger(self):
        
        logger = self.get_logger()
        
        fh = logging.FileHandler(self.log_file)
        fh.setLevel(logging.DEBUG)
        
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        
        # create formatter and add it to the handlers
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
            )
        console_formatter = logging.Formatter(
            '%(message)s'
            )
        ch.setFormatter(console_formatter)
        fh.setFormatter(file_formatter)
        # add the handlers to logger
        logger.addHandler(ch)
        logger.addHandler(fh)
        logger.propagate = 0
        
        
    def get_logger(self):
        logging.basicConfig(stream=sys.stdout)
        self.logger = logging.getLogger(self.logger_name)
        return self.logger
        
    def log(self, message, level="info"):
        message = self.logger_message_prefix + message
        if level in ["debug", "DEBUG"]:
            self.logger.debug(message)
        elif level in ["info", "INFO"]:
            self.logger.info(message)
        elif level in ["warning", "WARNING"]:
            self.logger.warning(message)
        elif level in ["error", "ERROR"]:
            self.logger.error(message)
        elif level in ["critical", "CRITICAL"]:
            self.logger.critical(message)
        else:
            raise Exception("{0} log level does not exist".format(level))

    def set_logger_message_prefix(self, prefix):
        if not self.logger_message_prefix_set:
            self.logger_message_prefix = prefix 
            self.logger_message_prefix_set = True
            
class ConfigAware(object):
    def convert_to_boolean(self, value):
        if value in ['true', "yes", "1", "on", True]:
            return True
        elif value in ['false', "no", "0", "off", False]:
            return False
        else:
            raise Exception("Can't convert value {0} to boolean".format(value))
        
def human_size(bytes):
    """
        Return a bit syze in human readable format
        from http://bjdierkes.com/python-converting-bytes-to-a-human-readable-format/
    """
    SYMBOLS = ('Kb', 'Mb', 'Gb', 'Tb', 'Pb', 'Eb', 'Zb', 'Yb')
    PREFIX = {}
    
    for i, s in enumerate(SYMBOLS):
        PREFIX[s] = 1 << (i+1)*10
    
    for s in reversed(SYMBOLS):
        if bytes >= PREFIX[s]:
            value = float(bytes) / PREFIX[s]
            return '%.1f%s' % (value, s)
    
    # bytes is less than 1024B
    return '%.1fB' % bytes
    
 
def folder_size(path, human=True):
    """
    from http://snipplr.com/view/47686/
    """
    total_size = os.path.getsize(path)
    for item in os.listdir(path):
        itempath = os.path.join(path, item)
        if os.path.isfile(itempath):
            total_size += os.path.getsize(itempath)
        elif os.path.isdir(itempath):
            total_size += folder_size(itempath, human=False)
    
    if human:
        ret = human_size(total_size)
    else:
        ret = total_size
    return ret