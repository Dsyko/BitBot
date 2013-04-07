__author__ = 'dsyko'

import MtGox
import Secret


Gox = MtGox.GoxRequester(Secret.gox_api_key, Secret.gox_auth_secret)

#print Gox.perform("BTCUSD/money/ticker", "")
#bid = buy, ask = sell BTC
#print Gox.trade_order("sell", .01, 1000)
#print Gox.account_info()
data = Gox.orders_info()
for order in data:
    print "%s %.2f BTC for $%.2f each" % (order['type'], order['num_btc'], order['usd_price'])
