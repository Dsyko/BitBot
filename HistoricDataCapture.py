__author__ = 'dsyko'

import MtGox
import json
import couchdb
import math
import time
from GetSecrets import gox_api_key, gox_auth_secret, couch_url, bitcoin_historic_data_db_name, bitcoin_historic_data_view_name



def pretty(text):
    return json.dumps(text, indent = 4, sort_keys = True)

class HistoricDataCapture:
    def __init__(self, api_interface, couch_interface):
        self.api_interface = api_interface
        self.couch_interface = couch_interface

    def gox_to_couchdb(self, start_time, end_time, time_interval):
        """

        :param start_time: microseconds since 1970(epoch) to start at
        :param end_time: microseconds since 1970(epoch) to end at
        :param time_interval: microseconds between data points trades will be grouped averaged
        """
        last_trade_time = start_time

        #Get a list of times already in the DB so we don't repeat ourselves
        times_entered_into_db = {}
        #We need to have a view to our couchDB which emits the time as the key in the Map function, mine is saved in Prices/time
        view_name = bitcoin_historic_data_view_name
        times_in_db = self.couch_interface.view(view_name)
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


#Following code will only be executed if this module is run independently, not when imported. Use it to test the module.
if __name__ == "__main__":

    #Creating instance of our MtGox api interface. Using API key and secret saved in Secret.py
    Gox = MtGox.GoxRequester(gox_api_key, gox_auth_secret)
    #Creating instance of our couchDB interface, using url(string) with login and pass saved in Secret.py
    couch = couchdb.Server(couch_url)

    #Start time and end time create bound which trade data will be added to our database
    start_time = 1364190193000000
    end_time = 1365292800000000
    #time_interval is in seconds, groups trades together within this interval and averages them to create a single datapoint
    time_interval = 60
    database = couch[bitcoin_historic_data_db_name]

    #Create an instance of HistoricDataCapture Class passing our API and DB interface instances
    TestHistoric = HistoricDataCapture(Gox, database)
    print "Calling gox_to_couchdb requesting trades between %s and %s. \n Then averaging them into %d second time intervals and saving them to the %s database on our CouchDB" % (time.ctime(int(start_time / 1e6)), time.ctime(int(end_time / 1e6)), time_interval, db_name)
    TestHistoric.gox_to_couchdb(start_time, end_time, time_interval * 1000000)
    print "Should be done now, go check couchDB for new Documents"