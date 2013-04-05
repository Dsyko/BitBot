__author__ = 'dsyko'

import MtGox
import Secret


Gox = MtGox.GoxRequester(Secret.api_key, Secret.auth_secret)

#print Gox.perform("BTCUSD/money/ticker", "")
#bid = buy, ask = sell BTC
#print Gox.trade_order("buy", .01, 10)
print Gox.account_info()