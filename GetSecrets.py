__author__ = 'dsyko'

import Secret
import os

#This keeps api keys and such secret(out of git repo) while still being able to deploy to Heroku(using env variables)
#Also falls back to local Secret.py file if doing development locally
gox_api_key = os.getenv('GOX_API_KEY', Secret.gox_api_key)
gox_auth_secret = os.getenv('GOX_API_SECRET', Secret.gox_auth_secret)
couch_url = os.getenv('COUCH_URL', Secret.couch_url)
bitcoin_historic_data_db_name = os.getenv('BITCOIN_HISTORIC_DATA_DB_NAME', Secret.bitcoin_historic_data_db_name)
bitcoin_historic_data_view_name = os.getenv('BITCOIN_HISTORIC_DATA_VIEW_NAME', Secret.bitcoin_historic_data_view_name)
logging_db_name = os.getenv('LOGGING_DB_NAME', Secret.logging_db_name)
