from fabfile import autosave

import logging

logger = logging.getLogger('autosave')
logger.setLevel(logging.DEBUG)

autosave()
