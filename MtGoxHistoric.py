__author__ = 'dsyko'
#The purpose of this module is as a drop-in replacement for the MtGox live API interface module. This module takes data
#from a couchDB containing historic Bitcoin prices so that we can feed the prices to our trading algorithm and
#test how it would have performed in the past.

#import libraries we'll need
import time
import json
import couchdb
from GetSecrets import couch_url, bitcoin_historic_data_db_name, bitcoin_historic_data_view_name



class HistoricGoxRequester:

    def __init__(self, couch_database, start_time, end_time, usd_balance, btc_balance):
        self.start_time = start_time
        self.start_time = end_time
        self.current_time = start_time
        self.usd_balance = usd_balance
        self.btc_balance = btc_balance
        self.couch_interface = couch_database.view(bitcoin_historic_data_view_name)
        self.price_list = self.couch_interface[start_time:end_time]
        self.current_price = 0
        self.trade_queue = []
        self.my_market_info_emitter = self.market_info_emitter()
        self.trade_fee = 0.6

    def execute_trades(self):
        #TODO: Add lag, and slippage simulation ability
        #check self.trade_queue for trades. If the price is right, execute that trade!
        for order in self.trade_queue:
            if order['type'] == 'buy' and (order['usd_price'] is None or self.current_price <= order['usd_price']):
                if self.usd_balance >= self.current_price * order['num_btc']:
                    self.btc_balance += order['num_btc']
                    self.btc_balance -= order['num_btc'] * (self.trade_fee / 100)
                    self.usd_balance -= self.current_price * order['num_btc']
                    self.trade_queue.remove(order)
            elif order['type'] == 'sell' and (order['usd_price'] is None or self.current_price >= order['usd_price']):
                if self.btc_balance >= order['num_btc']:
                    self.btc_balance -= order['num_btc']
                    self.usd_balance += self.current_price * order['num_btc']
                    self.usd_balance -= self.usd_balance * (self.trade_fee / 100)
                    self.trade_queue.remove(order)

    def market_info_emitter(self):
        for price in self.price_list:
            self.current_time = price.key
            self.current_price = price.value
            self.execute_trades()
            yield price.key, price.value
        yield False, False

    def account_info(self):
        return {'login_id': 'historic', 'trade_fee': self.trade_fee, 'btc_balance': self.btc_balance, 'usd_balance': self.usd_balance, 'api_rights': ["get_info", "trade"]}

    def trade_order(self, order_type, num_bitcoins, usd_price = None):
        """

        :param order_type: "buy" or "sell"
        :param num_bitcoins: number of bitcoins
        :param usd_price:  USD price of bitcoins or omit param for "market order"
        :return: Bool[True if trade order success, otherwise False], String[unique id of trade if successful]
        """
        #Add our trade to the trade queue, the trade queue is in execute_trade() to make trades when appropriate
        order_id = str((time.time()) * 1e6)
        self.trade_queue.append({'type': order_type, 'num_btc': num_bitcoins, 'usd_price': usd_price, 'order_id': order_id})
        return True, order_id


    def orders_info(self):
        """


        :return: A list of objects with structure [{"order_id": "unique id of order", "type": "buy or sell",
                                        "num_btc": "number of btc in order", "usd_price": "price per coin"}, ...]
        """
        return self.trade_queue

    def cancel_order_id(self, order_id):
        """


        :param order_id: unique id of order to cancel
        :return: json object returned by MtGox
        """
        for order in self.trade_queue:
            if order['order_id'] == order_id:
                self.trade_queue.remove(order)
        return True


    def cancel_order_by_type(self, order_type):
        """

        :param order_type: 'all', 'buy' or 'sell' specifies which orders to cancel
        :return: json object returned by MtGox
        """
        for order in self.trade_queue:
            if order_type == 'all' or order_type == order['type']:
                self.cancel_order_id(order['order_id'])

        return True

    def market_lag(self):
        return 0

    def market_info(self):
        #grab info from our market info emitter which is using couchDB to get market data
        trade_time, trade_price = next(self.my_market_info_emitter)
        if trade_time is not False:
            return {"time": trade_time, "volume": 0, "price": trade_price, "lag": self.market_lag()}

        return False

    def historic_data(self, start_time=None):
        """

        :param start_time: unix time stamp to begin getting (up to 24 hours of data) from gox
        """
        pass

#Following code will only be executed if this module is run independently, not when imported. Use it to test the module.
if __name__ == "__main__":



    def pretty(text):
        return json.dumps(text, indent = 4, sort_keys = True)

    #Creating instance of our historic prices from MtGox api interface.
    couch = couchdb.Server(couch_url)
    database = couch[bitcoin_historic_data_db_name]
    start_time = 1365292800000000
    end_time = 1365336000000000

    Gox = HistoricGoxRequester(database, start_time, end_time, 100, 0)

    #Get information on our account
    print "Account Info:"
    print pretty(Gox.account_info())

    #Get current market info
    print "\nThree market prices:"
    print pretty(Gox.market_info())
    print pretty(Gox.market_info())
    current_market_info = Gox.market_info()
    print pretty(current_market_info)

    #Add buy trade
    print "Adding trade order to buy $50 worth of BTC at market price"
    order_success, trade_id = Gox.trade_order("buy", (50 / current_market_info["price"]))
    if order_success:
        print "order has UID: %s" % trade_id
    else:
        print "Failed to submit order"

    print "Adding trade order to sell .1  BTC at $1000:"
    order_success, trade_id = Gox.trade_order("sell", .1, 1000)
    if order_success:
        print "order has UID: %s" % trade_id
    else:
        print "Failed to submit order"

    #Get trade orders
    print "Open orders:"
    print pretty(Gox.orders_info())


    #Get market info, which should execute open trades
    current_market_info = Gox.market_info()

    #Get information on our account
    print "Account Info:"
    print pretty(Gox.account_info())

    #Get trade orders
    print "Open orders:"
    print pretty(Gox.orders_info())







