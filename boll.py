from helper import Binance
from keys import api, secret
import ta
import pandas as pd
from time import sleep

session = Binance(api, secret)


def ema_band_stochastic(symbol):
    kl = session.klines(symbol, '15m')
    
    ema_50_high = ta.trend.ema_indicator(kl.High, window=50)
    ema_50_low = ta.trend.ema_indicator(kl.Low, window=50)
    ema_50_close = ta.trend.ema_indicator(kl.Close, window=50)
    ema_100_close = ta.trend.ema_indicator(kl.Close, window=100)
    
    stochastic = ta.momentum.StochasticOscillator(kl.High, kl.Low, kl.Close, window=14, smooth_window=3)
    
    # Long Entry
    if ema_50_close.iloc[-1] > ema_100_close.iloc[-1] and \
            all(ema_ > ema_100_close.iloc[-1] for ema_ in [ema_50_high.iloc[-1], ema_50_low.iloc[-1], ema_50_close.iloc[-1]]) and \
            stochastic.stoch_signal().iloc[-1] > 30 and stochastic.stoch().iloc[-1] > 50:
        return 'buy'
    
    # Short Entry
    elif ema_50_close.iloc[-1] < ema_100_close.iloc[-1] and \
            all(ema_ < ema_100_close.iloc[-1] for ema_ in [ema_50_high.iloc[-1], ema_50_low.iloc[-1], ema_50_close.iloc[-1]]) and \
            stochastic.stoch_signal().iloc[-1] > 70 and stochastic.stoch().iloc[-1] < 50:
        return 'sell'
    
    return None


tp = 0.012
sl = 0.009
qty = 10
leverage = 10
mode = 'ISOLATED'
max_pos = 50
symbols = session.get_tickers_usdt()

while True:
    try:
        balance = session.get_balance_usdt()
        print(f'Balance: {round(balance, 3)} USDT')
        
        positions = session.get_positions()
        orders = session.check_orders()
        print(f'{len(positions)} Positions: {positions}')

        for elem in orders:
            if elem not in positions:
                session.close_open_orders(elem)

        for symbol in symbols:
            positions = session.get_positions()
            if len(positions) >= max_pos:
                break
            sign = ema_band_stochastic(symbol)
            if sign is not None and symbol not in positions and symbol not in orders:
                print(symbol, sign)
                session.open_order_market(symbol, sign, qty, leverage, mode, tp, sl)
                sleep(1)

        wait = 300
        print(f'Waiting {wait} sec')
        sleep(wait)
    except Exception as err:
        print(err)
        sleep(30)
