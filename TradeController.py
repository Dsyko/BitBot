__author__ = 'dsyko'

import MtGox
import Secret
import couchdb
import math
import time
import numpy
from pylab import plot, ylim, xlim, show, xlabel, ylabel, grid



class TradeController:
    def __init__(self, api_interface, couch_interface):
        self.api_interface = api_interface
        self.couch_interface = couch_interface
        #Temporary variable to avoid spamming API with requests, del after we use the info
        account_info = api_interface.account_info()
        self.btc_balance = account_info['btc_balance']
        self.usd_balance = account_info['usd_balance']
        self.trade_fee = account_info['trade_fee']
        del account_info

        #TODO: Poll DB to get recent price information, enough for window. if it isn't in DB Fuck it we'll do it live, call historicData
        #TODO: Log trading start time to DB, keep a last_active variable up to date. log trades etc...

    def movingaverage(self, array, window_size):
        #TODO add different weightings
        #TODO try out PANDA library for time seres moving avg
        weightings = numpy.repeat(1.0, window_size) / window_size
        return numpy.convolve(array, weightings, 'same')

    #TODO: create a method to be called with newest price information
    # This method will compute moving average or whatever is desired and then trade BTC according to info

#Following code will only be run if this module is run independently
if __name__ == "__main__":
    import sys
    #Gox = MtGox.GoxRequester(Secret.gox_api_key, Secret.gox_auth_secret)
    couch = couchdb.Server(Secret.couch_url)
    database = couch['bitcoin-historic-data']

    print int(time.time() * 1e6)
    times = []
    price = []
    view_name = "Prices/time"
    start_time = 1364244060000000
    end_time = 1364256000000000
    times_in_db = database.view(view_name)
    for single_time in times_in_db[start_time:end_time]:
        times.append(single_time.key)
        price.append(single_time.value)

    plot(times, price)
    #y_av = movingaverage(y, 10)
    #plot(x, y_av,"r")
    #xlim(0,20)
    xlabel("Time, microseconds since 1970.")
    ylabel("Price of Bitcoin")
    grid(True)
    show()