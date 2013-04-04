__author__ = 'dsyko'

import MtGox
import Secret


Gox = MtGox.requester(Secret.api_key, Secret.auth_secret)

#print Gox.perform("BTCUSD/money/ticker", "")
#bid = buy, ask = sell BTC
print Gox.perform("BTCUSD/money/order/add", {"type" : "bid", "amount_int" : int(.01 * 1e8), "price_int" : int(10 * 1e5) })