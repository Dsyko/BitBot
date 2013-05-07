__author__ = 'dsyko'

#import libraries we'll need
from urllib import urlencode
import urllib2
import time
from hashlib import sha512
from hmac import HMAC
import base64
import json

#Decorator function used to catch HTTP errors and retry the request up to 5 times with throttling
def catch_http_errors(function):
    def catcher(*args, **kwargs):
        num_retries = 0
        while num_retries < 5:
            if num_retries > 0:
                time.sleep(5 * num_retries)
            try:
                result = function(*args, **kwargs)
            except urllib2.HTTPError as e:
                print 'HTTP Error code: %s: %s' % (e.code, e.msg)
                print "URL: %s" % e.filename
                num_retries += 1
                print "Retry Number: %d" % num_retries
            else:
                return result
        return False
    return catcher

def pretty(text):
        return json.dumps(text, indent = 4, sort_keys = True)

class GoxRequester:
    #TODO: Websockets version of this api

    def __init__(self, auth_key, auth_secret):
        self.auth_key = auth_key
        self.auth_secret = base64.b64decode(auth_secret)
        self.base = "https://data.mtgox.com/api/2/"

        #We need a nonce(one time use number to prevent repeat-requests and copycat attacks) for each API request
    def get_nonce(self):
        return int(time.time()*100000)

    def sign_data(self, data):
        return base64.b64encode(str(HMAC(self.auth_secret, data, sha512).digest()))

    def build_query(self, path, request = None):
        if request is None:
            request = {}
        request["nonce"] = self.get_nonce()
        post_data = urlencode(request)
        headers = {"User-Agent": "BitBot",
                   "Rest-Key": self.auth_key,
                   "Rest-Sign": self.sign_data(path + chr(0) + post_data)}
        return post_data, headers

    def send_http_request(self, path, args):
        data, headers = self.build_query(path, args)
        request = urllib2.Request(self.base + path, data, headers)
        response = urllib2.urlopen(request, data)
        return json.load(response)

    @catch_http_errors
    def account_info(self):
        data = self.send_http_request("BTCUSD/money/info", {})
        #print pretty(data)
        if data['result'] == "success":
            return {'login_id': data['data']["Login"],'trade_fee': data['data']["Trade_Fee"], 'btc_balance': float(data['data']["Wallets"]['BTC']['Balance']['value']), 'usd_balance': float(data['data']["Wallets"]['USD']['Balance']['value']), 'api_rights': data['data']["Rights"]}
        else:
            return False

    @catch_http_errors
    def trade_order(self, order_type, num_bitcoins, usd_price = None):
        """

        :param order_type: "buy" or "sell"
        :param num_bitcoins: number of bitcoins
        :param usd_price:  USD price of bitcoins or omit param for market order
        :return: Bool[True if trade order success, otherwise False], String[unique id of trade if successful]
        """
        args = {"amount_int" : int(num_bitcoins * 1e8)}
        if usd_price is not None:
            args["price_int"] = int(usd_price * 1e5)
        if order_type == "buy":
            args["type"] = "bid"
        if order_type == "sell":
            args["type"] = "ask"
        trade_result = self.send_http_request("BTCUSD/money/order/add", args)
        if trade_result['result'] == "success":
            return True, trade_result['data']
        else:
            return False, "No trade added"

    @catch_http_errors
    def orders_info(self):

        """


        :return: A list of objects with structure [{"order_id": "unique id of order", "type": "buy or sell",
                                        "num_btc": "number of btc in order", "usd_price": "price per coin"}, ...]
        """
        data = self.send_http_request("BTCUSD/money/orders", {})
        list_of_orders = []
        if data['result'] == 'success':
            for order in data['data']:
                order_to_add = {'order_id': order['oid']}

                if order['type'] == 'bid':
                    order_to_add['type'] = 'buy'
                else:
                    order_to_add['type'] = 'sell'

                order_to_add['num_btc'] = float(order['amount']['value'])
                order_to_add['usd_price'] = float(order['price']['value'])
                list_of_orders.append(order_to_add)

        return list_of_orders

    @catch_http_errors
    def cancel_order_id(self, order_id):
        """


        :param order_id: unique id of order to cancel
        :return: json object returned by MtGox
        """
        if self.send_http_request("BTCUSD/money/order/cancel", {"oid": str(order_id)})['result'] == "success":
            return True
        else:
            return False

    @catch_http_errors
    def cancel_order_by_type(self, order_type):
        """

        :param order_type: 'all', 'buy' or 'sell' specifies which orders to cancel
        :return: json object returned by MtGox
        """
        open_orders = self.orders_info()
        for order in open_orders:
            if order_type == 'all' or order_type == order['type']:
                if not (self.cancel_order_id(order['order_id'])):
                    return False
        return True

    @catch_http_errors
    def market_lag(self):
        data = self.send_http_request("BTCUSD/money/order/lag", {})
        if data['result'] == 'success':
            return data['data']['lag_secs']

    @catch_http_errors
    def market_info(self):
        data = self.send_http_request("BTCUSD/money/ticker", {})
        #print(pretty(data))
        return {"time": data["data"]["now"], "volume": float(data["data"]["vol"]["value"]), "price": float(data["data"]["last"]["value"]), "vwap": float(data["data"]["vwap"]["value"]), "lag": self.market_lag()}

    @catch_http_errors
    def historic_data(self, start_time=None):
        """

        :param start_time: unix time stamp to begin getting (up to 24 hours of data) from
        """

        args = {}
        if start_time is not None:
            args['since'] = start_time
        return self.send_http_request("BTCUSD/money/trades/fetch", args)

#Following code will only be executed if this module is run independently, not when imported. Use it to test the module.
if __name__ == "__main__":

    import Secret

    def pretty(text):
        return json.dumps(text, indent = 4, sort_keys = True)

    #Creating instance of our MtGox api interface. Using API key and secret saved in Secret.py
    Gox = GoxRequester(Secret.gox_api_key, Secret.gox_auth_secret)

    #Get information on our account
    print pretty(Gox.account_info())

    #Get current market info
    print pretty(Gox.market_info())

    """
    successful_order = False
    while not successful_order:
        successful_order = Gox.trade_order("buy", 2.05, 195)[0]
    print pretty(Gox.orders_info())
    #print Gox.cancel_order_by_type("sell")
    """
