import MetaTrader5 as mt
import pandas as pd
import time
import numpy as np
from datetime import datetime

# Connect to MetaTrader 5
mt.initialize()

login = 51808202
password = "@ZmqeTY44B3!6N"
server = "ICMarketsSC-Demo"

mt.login(login, password, server)


ticker = 'BTCUSD'  # example ticker
qty = 0.1  # example quantity
buy_order_type = mt.ORDER_TYPE_BUY
sell_order_type = mt.ORDER_TYPE_SELL

def fetch_ohlcv(ticker):
    return pd.DataFrame(mt.copy_rates_range(ticker, mt.TIMEFRAME_M1, datetime(2024, 5, 1), datetime.now()))



def calculate_fibonacci_levels(high, low):
    diff = high - low
    return {
        'level_0': low,
        'level_1': low + 0.236 * diff,
        'level_2': low + 0.382 * diff,
        'level_3': low + 0.5 * diff,
        'level_4': low + 0.618 * diff,
        'level_5': high
    }

def identify_order_blocks(df):
    order_blocks = []
    for i in range(1, len(df) - 1):
        if df['low'][i] < df['low'][i-1] and df['low'][i] < df['low'][i+1]:
            order_blocks.append((df['time'][i], df['low'][i]))
        if df['high'][i] > df['high'][i-1] and df['high'][i] > df['high'][i+1]:
            order_blocks.append((df['time'][i], df['high'][i]))
    return order_blocks

def identify_fair_value_gaps(df):
    gaps = []
    for i in range(2, len(df)):
        if df['low'][i] > df['high'][i-2]:
            gaps.append((df['time'][i], df['low'][i], df['high'][i-2]))
    return gaps

def create_order(ticker, qty, order_type, price, sl=None, tp=None):
    request = {
        "action": mt.TRADE_ACTION_DEAL,
        "symbol": ticker,
        "volume": qty,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 10,
        "magic": 234000,
        "comment": "python script open",
        "type_time": mt.ORDER_TIME_GTC,
        "type_filling": mt.ORDER_FILLING_RETURN,
    }
    result = mt.order_send(request)
    return result

def close_order(ticker, qty, order_type, price):
    positions = mt.positions_get(symbol=ticker)
    for pos in positions:
        request = {
            "action": mt.TRADE_ACTION_DEAL,
            "symbol": ticker,
            "volume": qty,
            "type": order_type,
            "position": pos.ticket,
            "price": price,
            "deviation": 10,
            "magic": 234000,
            "comment": "python script close",
            "type_time": mt.ORDER_TIME_GTC,
            "type_filling": mt.ORDER_FILLING_RETURN,
        }
        result = mt.order_send(request)
    return result

for i in range(100):
    ohlc = fetch_ohlcv(ticker)
    ohlc['time'] = pd.to_datetime(ohlc['time'], unit='s')
    print(ohlc)
    
    fib_levels = calculate_fibonacci_levels(ohlc['high'].max(), ohlc['low'].min())
    order_blocks = identify_order_blocks(ohlc)
    fair_value_gaps = identify_fair_value_gaps(ohlc)
    
    current_close = ohlc.iloc[-1]['close']
    last_close = ohlc.iloc[-2]['close']
    last_high = ohlc.iloc[-2]['high']
    last_low = ohlc.iloc[-2]['low']
    
    long_condition = current_close > last_high
    short_condition = current_close < last_low
    closelong_condition = current_close < last_close
    closeshort_condition = current_close > last_close

    already_buy = False
    already_sell = False

    try:
        positions = mt.positions_get()
        if positions:
            already_sell = positions[0]._asdict()['type'] == mt.ORDER_TYPE_SELL
            already_buy = positions[0]._asdict()['type'] == mt.ORDER_TYPE_BUY
    except:
        pass

    no_positions = len(mt.positions_get()) == 0

    if long_condition:
        if no_positions:
            create_order(ticker, qty, buy_order_type, current_close)
            print("Buy Order Placed")
        if already_sell:
            close_order(ticker, qty, buy_order_type, current_close)
            print("Sell Position Closed")
            time.sleep(1)
            create_order(ticker, qty, buy_order_type, current_close)
            print("Buy Order Placed")
    if short_condition:
        if no_positions:
            create_order(ticker, qty, sell_order_type, current_close)
            print("Sell Order Placed")
        if already_buy:
            close_order(ticker, qty, sell_order_type, current_close)
            print("Buy Position Closed")
            time.sleep(1)
            create_order(ticker, qty, sell_order_type, current_close)
            print("Sell Order Placed")

    try:
        positions = mt.positions_get()
        if positions:
            already_sell = positions[0]._asdict()['type'] == mt.ORDER_TYPE_SELL
            already_buy = positions[0]._asdict()['type'] == mt.ORDER_TYPE_BUY
    except:
        pass

    if closelong_condition and already_buy:
        close_order(ticker, qty, sell_order_type, current_close)
        print("Only Buy Position Closed")
    if closeshort_condition and already_sell:
        close_order(ticker, qty, buy_order_type, current_close)
        print("Only Sell Position Closed")

    already_buy = False
    already_sell = False
    time.sleep(60)
