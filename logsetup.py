__author__ = 'dsyko'

import logging
import logging.handlers
from GetSecrets import couch_url,logging_db_name, bitcoin_historic_data_db_name, bitcoin_historic_data_view_name

#lets use logging to keep track of our bit-bot's status. either to console or to a couchdb

# create logger
logger = logging.getLogger('bitbot_logs')
logger.setLevel(logging.DEBUG)

streamhandler = logging.StreamHandler()
streamhandler.setLevel(logging.DEBUG)

#we're gonna need to write our own loghandler to log to couchDB

logger.addHandler(streamhandler)

logger.warning("derp!")


