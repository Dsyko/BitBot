__author__ = 'dsyko'

import MtGox
import Secret
import couchdb
import math
import time
import numpy
import pandas as pd
import HistoricData
from pylab import plot, ylim, xlim, show, xlabel, ylabel, grid



class TradeController:
    def __init__(self, api_interface, couch_interface, run_id, window_size_minutes):
        """

        :param api_interface: MtGox or HistoricTesting API
        :param couch_interface: interface to our couchDB
        :param run_id: unique string, used when logging trade outcomes
        :param window_size_minutes: number of minutes used in our moving average window
        """
        self.api_interface = api_interface
        self.couch_interface = couch_interface
        self.run_id = run_id
        self.window_size = window_size_minutes
        #Temporary variable to avoid spamming API with requests, del after we use the info
        account_info = api_interface.account_info()
        self.btc_balance = account_info['btc_balance']
        self.usd_balance = account_info['usd_balance']
        self.trade_fee = account_info['trade_fee']
        del account_info
        self.btc_price = {}
        #Get historic data from DB so we can compute our window
        times_in_db = couch_interface.view("Prices/time")
        start_time = int(time.time() * 1e6) - ( 3 * window_size_minutes * 60000000)
        end_time = int(time.time() * 1e6)
        print times_in_db[start_time:end_time]
        #TODO: Poll DB to get recent price information, enough for window. if it isn't in DB Fuck it we'll do it live, call historicData
        #TODO: Log trading start time to DB, keep a last_active variable up to date. log trades etc...

    def movingaverage(self, array, window_size):
        #TODO add different weightings
        #TODO try out PANDA library for time seres moving avg
        weightings = numpy.repeat(1.0, window_size) / window_size
        return numpy.convolve(array, weightings, 'same')

    #TODO: create a method to be called with newest price information
    # This method will compute moving average or whatever is desired and then trade BTC according to info

#Following code will only be executed if this module is run independently, not when imported. Use it to test the module.
if __name__ == "__main__":
    import sys
    Gox = MtGox.GoxRequester(Secret.gox_api_key, Secret.gox_auth_secret)
    couch = couchdb.Server(Secret.couch_url)
    database = couch['bitcoin-historic-data']

    times = []
    price = []
    view_name = "Prices/time"
    window_size = 600
    end_time = 1356393600000000
    start_time = end_time - (window_size * 60000000)
    times_in_db = database.view(view_name)
    temp_time_window = times_in_db[start_time:end_time]
    if len(temp_time_window) < window_size:
        print "Grabbing info from Gox only have %d points need %d" % (len(temp_time_window), window_size)
        TestHistoric = HistoricData.HistoricData(Gox, database)
        TestHistoric.gox_to_couchdb(start_time, end_time, 60 * 1000000)
        temp_time_window = times_in_db[start_time:end_time]
        print "now we have %d points" % len(temp_time_window)

    """
    captured_times = [derp.key for derp in testing]
    captured_prices = [derp.value for derp in testing]
    #print len(testing2)
    #print testing2
    series = pd.Series(captured_prices, captured_times, name="bitcoinprice")
    #print series
    #series = series.cumsum()
    #print series
    series.plot(style='k--')
    pd.rolling_mean(series, window_size).plot(style='b')
    pd.ewma(series, window_size).plot(style='r-')
    pd.ewma(series, window_size/2).plot(style='g-')
    show()
    """

    """
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
        """