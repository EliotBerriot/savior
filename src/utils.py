
import logging
import sys
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