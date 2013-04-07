__author__ = 'dsyko'

import MtGox
import Secret
import json
import couchdb
import math

def pretty(text):
    return json.dumps(text, indent = 4, sort_keys = True)

class HistoricDataCapture:
    def __init__(self, api_interface):
        self.api_interface = api_interface

    def GoxToCouch(self, start_time, end_time, time_interval):
        """

        :param start_time: milliseconds since 1970 to start at
        :param end_time: milliseconds since 1970 to end at
        :param time_interval: milliseconds between data points
        """
        last_trade_time = start_time
        times_entered_into_db = {}

        while last_trade_time < end_time:
            raw_trades = self.api_interface.historic_data(last_trade_time)
            previous_request_start_time = last_trade_time
            #print pretty(raw_trades)
            trades_grouped_by_time = {}
            for trade in raw_trades["data"]:
                if trade["primary"] == "Y":
                    #divide by the time_interval and use floor to cut off unused milliseconds,
                    # then multiply by time_interval to get back to proper timestamp
                    quantized_trade_time = int(math.floor(int(trade['tid']) / time_interval) * time_interval)
                    if trades_grouped_by_time.get(quantized_trade_time, False):
                        trades_grouped_by_time[quantized_trade_time].append(trade["price_int"])
                    else:
                        trades_grouped_by_time[quantized_trade_time] = [trade["price_int"]]
                     #Keep track of our last trade timestamp
                    if last_trade_time < int(trade['tid']):
                        last_trade_time = int(trade['tid'])

            print pretty(trades_grouped_by_time)
            #print pretty(raw_trades)

            #If our last_trade_time hasn't advanced since our last call to the API add a day so we don't get stuck
            if previous_request_start_time >= last_trade_time:
                last_trade_time += 86400000000
            last_trade_time = end_time







Gox = MtGox.GoxRequester(Secret.gox_api_key, Secret.gox_auth_secret)
couch = couchdb.Server(Secret.couch_url)
database = couch['bitcoin-historic-data']

TestHistoric = HistoricDataCapture(Gox)
TestHistoric.GoxToCouch(1365329850000000, 1365337050000000, 60 * 1000000)