__author__ = 'dsyko'

import MtGox
import Secret
import json
import couchdb
import math
import time


def pretty(text):
    return json.dumps(text, indent = 4, sort_keys = True)

class HistoricDataCapture:
    def __init__(self, api_interface, couch_interface):
        self.api_interface = api_interface
        self.couch_interface = couch_interface

    def GoxToCouch(self, start_time, end_time, time_interval):
        """

        :param start_time: microseconds since 1970(epoch) to start at
        :param end_time: microseconds since 1970(epoch) to end at
        :param time_interval: microseconds between data points trades will be grouped averaged
        """
        last_trade_time = start_time

        #Get a list of times already in the DB so we don't repeat ourselves
        times_entered_into_db = {}
        #We need to have a view to our couchDB which emits the time as the key in the Map function, mine is saved in Prices/time
        viewname = "Prices/time"
        times_in_db = self.couch_interface.view(viewname)
        for single_time in times_in_db[start_time:end_time]:
            times_entered_into_db[single_time.key] = True
        #print times_entered_into_db

        while last_trade_time < end_time:
            print "requesting trades starting at: " + time.ctime(int(last_trade_time / 1e6))
            raw_trades = self.api_interface.historic_data(last_trade_time)
            previous_request_start_time = last_trade_time
            #print pretty(raw_trades)
            trades_grouped_by_time = {}
            for trade in raw_trades["data"]:
                if trade["primary"] == "Y":
                    #divide by the time_interval and use floor to cut off(round down) unused microseconds,
                    # then multiply by time_interval to get back to proper timestamp
                    quantized_trade_time = int(math.floor(int(trade['tid']) / time_interval) * time_interval)
                    if trades_grouped_by_time.get(quantized_trade_time, False):
                        trades_grouped_by_time[quantized_trade_time].append(int(trade["price_int"]))
                    else:
                        trades_grouped_by_time[quantized_trade_time] = [int(trade["price_int"])]
                     #Keep track of our last trade timestamp
                    if last_trade_time < int(trade['tid']):
                        last_trade_time = int(trade['tid'])

            #Put avg price per interval into couchDB
            for trade_time, price_array in trades_grouped_by_time.iteritems():
                if not times_entered_into_db.get(trade_time, False):
                    times_entered_into_db[trade_time] = True
                    self.couch_interface.save({'time': trade_time, 'price': sum(price_array)/ (len(price_array) * 1.0e5)})

            #If our last_trade_time hasn't advanced since our last call to the API add a day so we don't get stuck
            if previous_request_start_time >= last_trade_time:
                last_trade_time += 86400000000
            









Gox = MtGox.GoxRequester(Secret.gox_api_key, Secret.gox_auth_secret)
couch = couchdb.Server(Secret.couch_url)
database = couch['bitcoin-historic-data']

TestHistoric = HistoricDataCapture(Gox, database)
TestHistoric.GoxToCouch(1364169600000000, 1364774400000000, 60 * 1000000)