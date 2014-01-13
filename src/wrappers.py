from errors import CheckConfigError

def need_config_check(func):
    """
        A wrapper for function that need a config check before be run
    """
    def wrapper(self, *args, **kwargs): 
        try:
        	self.check_config()
        except CheckConfigError, e:
        	if self.send_mail:
        		self.mail()

        	self.log("Savior will end now.")
        else:
        	func(self, *args, **kwargs)

    return wrapper