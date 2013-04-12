__author__ = 'dsyko'

import MtGox
import Secret
import couchdb
import json
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
        self.run_id = str(run_id)
        #Check if we have a database by this name on couch, if so append time stamp to name
        if self.run_id in self.couch_interface:
            self.run_id += "-" + str(int(time.time() * 1e6))
        print "Logging trade info in %s db on couchDB" % self.run_id
        self.log_database = self.couch_interface.create(self.run_id)


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
        historic_data = self.couch_interface['bitcoin-historic-data']
        times_in_db = historic_data.view("Prices/time")
        temp_time_window = times_in_db[start_time:end_time]

        #Not enough values in DB. Fuck it we'll do it live, call historicData to get info from GOX into DB
        if len(temp_time_window) < window_size_minutes:
            #TODO: test if this is a live trade or historic test, if historic try reaching farther back in DB before GOX
            print "Grabbing info from Gox only have %d points need %d" % (len(temp_time_window), window_size_minutes)
            Historic = HistoricDataCapture.HistoricDataCapture(self.api_interface, historic_data)
            Historic.gox_to_couchdb(start_time, end_time, 60 * 1000000)
            temp_time_window = times_in_db[start_time:end_time]
            print "now we have %d points" % len(temp_time_window)

        recent_times = [trade_val.key for trade_val in temp_time_window]
        recent_prices = [trade_val.value for trade_val in temp_time_window]
        #self.recent_price_info = pd.Series(recent_prices, [pd.Timestamp(usecond_time *1000) for usecond_time in recent_times ], name="bitcoinprice")
        self.recent_price_info = pd.Series(recent_prices, recent_times, name="bitcoinprice")

        #Convert keys from integers to strings so we can convert to json and save in couchDB
        json_price_info = {str(the_time): the_price for the_time, the_price in self.recent_price_info.to_dict().iteritems()}
        self.log_database[str(int(time.time() * 1e6))] = {'init_time': int(time.time() * 1e6), 'init_price_info': json_price_info}
        return self.recent_price_info

    #Ohh god it's crashing! Sell it alllll!
    def sell_sell_sell(self):
        pass
        #TODO: check our balances, if we have bitcoin, sell it off
        #TODO: check status of trade orders, try again if they haven't gone through, throttle according to trading lag
        #TODO: log our sell to DB

    #Shit we're going to miss out on this huge price jump, buy all the bits coins. The Chickun arises!
    def buy_buy_buy(self):
        pass
        #TODO: check our balances, if we have USD, buy BTC
        #TODO: check status of trade orders, try again if they haven't gone through, throttle according to trading lag
        #TODO: log our buy to DB

    #call this function with updates market info, this is where all the decisions are made
    def market_info_feed(self, market_info, averaging_function, **kwargs ):
        pass
        #TODO: Add market_info into our series
        #TODO: Delete oldest data point in series to keep it small
        #TODO: Compute averaging function on series
        #TODO: Compute slope at last 2-4 points
        #TODO: Use slope, possibly market Depth info, and decide to sell or buy

    #update historic db with price info?

#Following code will only be executed if this module is run independently, not when imported. Use it to test the module.
if __name__ == "__main__":

    Gox = MtGox.GoxRequester(Secret.gox_api_key, Secret.gox_auth_secret)
    couch = couchdb.Server(Secret.couch_url)

    Trader = TradeController(Gox, couch, "testing")
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

