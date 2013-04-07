__author__ = 'dsyko'

import MtGox
import Secret
import json
import couchdb

def pretty(text):
    return json.dumps(text, indent = 4, sort_keys = True)

Gox = MtGox.GoxRequester(Secret.gox_api_key, Secret.gox_auth_secret)
couch = couchdb.Server(Secret.couch_url)
database = couch['bitcoin-historic-data']

#print Gox.perform("BTCUSD/money/ticker", "")


#print Gox.trade_order("sell", .01, 1000)

#print Gox.account_info()

#data = Gox.orders_info()
#for order in data:
#    print "id: %s %s %.2f BTC for $%.2f each" % (order['order_id'], order['type'], order['num_btc'], order['usd_price'])

#market_info = Gox.market_info()
#print pretty(market_info)
#print database.save(market_info)

#print pretty(Gox.historic_data())