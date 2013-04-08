__author__ = 'dsyko'

#import libraries we'll need
from urllib import urlencode
import urllib2
import time
from hashlib import sha512
from hmac import HMAC
import base64
import json

#We need a nonce(one time use number to prevent repeat-requests and copycat attacks) for each API request
def get_nonce():
    return int(time.time()*100000)

def sign_data(secret, data):
    return base64.b64encode(str(HMAC(secret, data, sha512).digest()))

class GoxRequester:
    #TODO: Handle errors related to API request errors and server down errors
    #TODO: Websockets version of this api
    def __init__(self, auth_key, auth_secret):
        self.auth_key = auth_key
        self.auth_secret = base64.b64decode(auth_secret)
        self.base = "https://data.mtgox.com/api/2/"

    def build_query(self, path, request=None):
        if not request: request = {}
        request["nonce"] = get_nonce()
        post_data = urlencode(request)
        headers = {"User-Agent": "BitBot",
                   "Rest-Key": self.auth_key,
                   "Rest-Sign": sign_data(self.auth_secret, path + chr(0) + post_data)} #API2 uses Path in hash
        return post_data, headers

    def send_request(self, path, args):
        data, headers = self.build_query(path, args)
        request = urllib2.Request(self.base + path, data, headers)
        response = urllib2.urlopen(request, data)
        return json.load(response)


    def trade_order(self, ordertype, bitcoins, price=None):
        """

        :param ordertype: "buy" or "sell"
        :param bitcoins: number of bitcoins
        :param price:  USD price of bitcoins or omit param for market order
        :return: json value returned by API result success or fail plus data containing ID of order id successful
        """
        args = {"amount_int" : int(bitcoins * 1e8)}
        if price:
            args["price_int"] = int(price * 1e5)
        if ordertype == "buy":
            args["type"] = "bid"
        if ordertype == "sell":
            args["type"] = "ask"

        return self.send_request("BTCUSD/money/order/add", args)

    def account_info(self):
        return self.send_request("BTCUSD/money/info", {})

    def orders_info(self):

        """


        :return: A list of objects with structure [{"order_id": "unique id of order", "type": "buy or sell",
                                        "num_btc": "number of btc in order", "usd_price": "price per coin"}, ...]
        """
        data = self.send_request("BTCUSD/money/orders", {})
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

    def cancel_order_id(self, order_id):
        """


        :param order_id: unique id of order to cancel
        :return: json object returned by MtGox
        """
        return self.send_request("BTCUSD/money/order/cancel", {"oid": str(order_id)})


    def cancel_order_by_type(self, order_type):
        """

        :param order_type: 'all', 'buy' or 'sell' specifies which orders to cancel
        :return: json object returned by MtGox
        """
        open_orders = self.orders_info()
        for order in open_orders:
            if order_type == 'all' or order_type == order['type']:
                return self.cancel_order_id(order['order_id'])
    def market_lag(self):
        data = self.send_request("BTCUSD/money/order/lag", {})
        if data['result'] == 'success':
            return data['data']['lag_secs']

    def market_info(self):
        data = self.send_request("BTCUSD/money/ticker", {})
        return {"time": data["data"]["now"], "volume": float(data["data"]["vol"]["value"]), "price": float(data["data"]["last"]["value"]), "vwap": float(data["data"]["vwap"]["value"]), "lag": self.market_lag()}

    def historic_data(self, start_time=None):
        """

        :param start_time: unix time stamp to begin getting 24 hours of data from
        """

        args = {}
        if start_time:
            args['since'] = start_time
        return self.send_request("BTCUSD/money/trades/fetch", args)
