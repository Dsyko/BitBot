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

    def perform(self, path, args):
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

        return self.perform("BTCUSD/money/order/add", args)

    def account_info(self):
        return self.perform("BTCUSD/money/info", {})