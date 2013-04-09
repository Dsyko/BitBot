__author__ = 'dsyko'

import MtGox
import Secret
import json
import couchdb
import time

def pretty(text):
    return json.dumps(text, indent = 4, sort_keys = True)

Gox = MtGox.GoxRequester(Secret.gox_api_key, Secret.gox_auth_secret)
couch = couchdb.Server(Secret.couch_url)
database = couch['bitcoin-historic-data']

#print Gox.perform("BTCUSD/money/ticker", "")


#print Gox.trade_order("sell", .01, 1000)

print pretty(Gox.account_info())
#print pretty(Gox.orders_info())
#print Gox.cancel_order_id("a08c8df4-633f-4855-bd03-f20e46a26abc")
#print Gox.cancel_order_by_type("sell")
#data = Gox.orders_info()
#for order in data:
#    print "id: %s %s %.2f BTC for $%.2f each" % (order['order_id'], order['type'], order['num_btc'], order['usd_price'])

#market_info = Gox.market_info()
#print pretty(market_info)
#results = database.view("Prices/time")
#print list(results[1365329880000000:1365330600000000])
#for time in results[1365329880000000:1365330600000000]:
#    print time.value
#print time.ctime(int("1365202"))
#print pretty(Gox.historic_data())