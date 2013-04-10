__author__ = 'dsyko'

import MtGox
import Secret
import couchdb
import math
import time
import numpy
import pandas as pd
import HistoricDataCapture
from pylab import plot, ylim, xlim, show, xlabel, ylabel, grid



class TradeController:
    def __init__(self, api_interface, couch_interface, run_id):
        """

        :param api_interface: MtGox or HistoricTesting API
        :param couch_interface: interface to our couchDB
        :param run_id: unique string, used when logging trade outcomes
        """
        self.api_interface = api_interface
        self.couch_interface = couch_interface
        self.run_id = run_id
        #Temporary variable to avoid spamming API with requests, del after we use the info
        account_info = api_interface.account_info()
        self.btc_balance = account_info['btc_balance']
        self.usd_balance = account_info['usd_balance']
        self.trade_fee = account_info['trade_fee']
        del account_info
        self.btc_price = {}
        self.recent_price_info = pd.Series()

    def initialize_price_info(self, trade_start_time, window_size_minutes):

        #Get historic data from couchDB so we can compute our windowed moving avg, or other stats
        #We will ask for price values ending at the time we want to start trading, going back to fill the window
        end_time = trade_start_time
        #Going back 4 times the window size, sometimes there are no trades for a few minutes
        start_time = trade_start_time - (4 * window_size_minutes * 60000000)

        times_in_db = self.couch_interface.view("Prices/time")
        temp_time_window = times_in_db[start_time:end_time]

        #Not enough values in DB. Fuck it we'll do it live, call historicData to get info from GOX into DB
        if len(temp_time_window) < window_size_minutes:
            #TODO: test if this is a live trade or historic test, if historic try reaching farther back in DB before GOX
            print "Grabbing info from Gox only have %d points need %d" % (len(temp_time_window), window_size_minutes)
            Historic = HistoricDataCapture.HistoricDataCapture(Gox, database)
            Historic.gox_to_couchdb(start_time, end_time, 60 * 1000000)
            temp_time_window = times_in_db[start_time:end_time]
            print "now we have %d points" % len(temp_time_window)

        recent_times = [trade_val.key for trade_val in temp_time_window]
        recent_prices = [trade_val.value for trade_val in temp_time_window]
        self.recent_price_info = pd.Series(recent_prices, recent_times, name="bitcoinprice")
        return self.recent_price_info

        #TODO: Create db on couch with run_id, save opening price
        #TODO: Log trading start time to DB, keep a last_active variable up to date. log trades etc...


    #TODO: create a method to be called with newest price information
    # This method will compute moving average or whatever is desired and then trade BTC according to info
    # update run_id database with trade decisions, value of accounts, etc
    #update historic db with price info?

#Following code will only be executed if this module is run independently, not when imported. Use it to test the module.
if __name__ == "__main__":

    Gox = MtGox.GoxRequester(Secret.gox_api_key, Secret.gox_auth_secret)
    couch = couchdb.Server(Secret.couch_url)
    database = couch['bitcoin-historic-data']

    Trader = TradeController(Gox, database, "test")
    Trader.initialize_price_info(1356393600000000, 40).plot(style='k--')
    show()

    """
    #print series
    #print series
    series.plot(style='k--')
    pd.rolling_mean(series, window_size).plot(style='b')
    pd.ewma(series, window_size).plot(style='r-')
    pd.ewma(series, window_size/2).plot(style='g-')
    show()
    """

