__author__ = 'dsyko'

import MtGox
import Secret
import couchdb
import time
import pandas as pd
import HistoricDataCapture
from pylab import plot, ylim, xlim, show, xlabel, ylabel, grid



class TradeController:
    def __init__(self, api_interface, couch_interface, run_id):
        """

        :param api_interface: MtGox or HistoricTesting API
        :param couch_interface: interface to our couchDB
        :param run_id: unique string, used when logging trade outcomes to couchDB
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
        account_info = self.api_interface.account_info()
        self.btc_balance = account_info['btc_balance']
        self.usd_balance = account_info['usd_balance']
        self.trade_fee = account_info['trade_fee']
        del account_info
        self.btc_price = {}
        self.recent_price_info = pd.Series()
        self.last_trade_attempt = 0

        self.averaging_functions = {
            "simple_moving": pd.rolling_mean,
            "exponential_moving": pd.ewma
        }

    def initialize_price_info(self, trade_start_time, window_size_minutes, update_from_gox):

        #Get historic data from couchDB so we can compute our windowed moving avg, or other stats
        #We will ask for price values ending at the time we want to start trading, going back to fill the window
        """

        :param trade_start_time: microsecond time stamp at which trading will begin
        :param window_size_minutes: how far back to grab data from, starting at trade_start_time
        :param update_from_gox: True or False, if True and there isn't enough data in couchDB grab data from MtGox
        :return: None
        """
        end_time = trade_start_time
        #Going back 4 times the window size, sometimes there are no trades for a few minutes
        start_time = trade_start_time - (4 * window_size_minutes * 60000000)
        historic_data = self.couch_interface['bitcoin-historic-data']
        times_in_db = historic_data.view("Prices/time")
        temp_time_window = times_in_db[start_time:end_time]

        #Not enough values in DB. Fuck it we'll do it live, call historicData to get info from GOX into DB
        if len(temp_time_window) < window_size_minutes:

            if update_from_gox:
                print "Grabbing info from Gox only have %d points need %d" % (len(temp_time_window), window_size_minutes)
                Historic = HistoricDataCapture.HistoricDataCapture(self.api_interface, historic_data)
                Historic.gox_to_couchdb(start_time, end_time, 60 * 1e6)
            else:
                #don't want to update from GOX, just grab more data from couchDB
                print "Grabbing more data from couchDB only have %d points need %d" % (len(temp_time_window), window_size_minutes)
                start_time -= (4 * window_size_minutes * 60000000)

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

    def log_trade_order(self, result, order_type,  num_btc, price):
        if result:
            self.log_database[str(int(time.time() * 1e6))] = {'trade_added': {'type': order_type, 'num_btc': num_btc, 'usd_price': price}}
        else:
            self.log_database[str(int(time.time() * 1e6))] = {'trade_fail': {'type': order_type,'num_btc': num_btc, 'usd_price': price}}

    #Ohh god it's crashing! Sell it alllll!
    #Shit we're going to miss out on this huge price jump, buy all the bits coins. The Chickun arises!
    def trade_trade_trade(self, trade_type):
        #grab account holdings from Gox
        account_info = self.api_interface.account_info()
        self.btc_balance = account_info['btc_balance']
        self.usd_balance = account_info['usd_balance']

        if trade_type == 'sell':
            currency_to_dump = self.btc_balance
        else:
            currency_to_dump = self.usd_balance

        seconds_between_trades = 60 #one minute between trades
        #seconds_between_trades = int(self.api_interface.market_lag()) #wait full market lag before trading again
        #check our balance, if we have bitcoin, sell it off, throttle trade attempts using seconds_between_trades
        if currency_to_dump > 0 and (int(time.time() * 1e6) - self.last_trade_attempt) > (seconds_between_trades * 1e6):
            success, trade_id = self.api_interface.trade_order(trade_type, self.btc_balance)
            self.last_trade_attempt = int(time.time() * 1e6)
            self.log_trade_order(self, success, trade_type, self.btc_balance, "market")

            #update account holdings from Gox
            account_info = self.api_interface.account_info()
            self.btc_balance = account_info['btc_balance']
            self.usd_balance = account_info['usd_balance']

        #TODO: check status of trade orders, try again if they haven't gone through, throttle according to trading lag
        #TODO: log our sell to DB


    #call this function with updates market info, this is where all the decisions are made
    def market_info_feed(self, market_info, averaging_function, averaging_window, **kwargs ):
        #Add market_info into our series
        self.recent_price_info.append(pd.Series({market_info['time']: market_info['price']}))
        #TODO: Delete oldest data point in series to keep it small
        self.recent_price_info = self.recent_price_info[1:]
        #TODO: Compute averaging function on series
        zveraged_prices = self.averaging_functions[averaging_function](self.recent_price_info, averaging_window)
        #TODO: Compute slope at last 2-4 points
        #TODO: Use slope, possibly market Depth info, and decide to sell or buy

    #update historic db with price info?

#Following code will only be executed if this module is run independently, not when imported. Use it to test the module.
if __name__ == "__main__":

    Gox = MtGox.GoxRequester(Secret.gox_api_key, Secret.gox_auth_secret)
    couch = couchdb.Server(Secret.couch_url)

    Trader = TradeController(Gox, couch, "testing")
    window_size = 60
    init_series = Trader.initialize_price_info(1356393600000000, window_size * 24, False)


    #print series
    #print series
    init_series.plot(style='k--')
    pd.rolling_mean(init_series, window_size).plot(style='b')
    pd.ewma(init_series, window_size).plot(style='r-')
    pd.ewma(init_series, span=window_size).plot(style='g-')
    show()


