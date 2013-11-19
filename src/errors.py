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
