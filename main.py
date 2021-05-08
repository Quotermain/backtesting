from __future__ import (
    absolute_import, division, print_function, unicode_literals
)

from utils.calculate_trade_size import calculate_trade_size
import backtrader as bt
import backtrader.feeds as btfeeds
import csv
import pickle
from time import sleep
from sys import argv

data_path = '../correction_advisor/data/thresholds/'
with open('data/ticker_info.pickle', 'rb') as file:
    ticker_info = pickle.load(file)
with open(data_path + 'open_close_hour_dif_mean.pickle', 'rb') as file:
    open_close_hour_dif_mean = pickle.load(file)
with open(data_path + 'open_close_hour_dif_std.pickle', 'rb') as file:
    open_close_hour_dif_std = pickle.load(file)

class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.datetime(0)
        print('%s, %s' % (dt, txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.dataopen_60min = self.datas[0].open

        # To keep track of pending orders
        self.order = None
        # Indicators
        self.rsi_60min = bt.indicators.RSI(self.datas[0])
        self.bolinger = bt.indicators.BBands(self.datas[0])


    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f'BUY EXECUTED, Price: {order.executed.price}, ' +
                    f'Cost: {order.executed.value}, ' +
                    f'Comm: {order.executed.comm}'
                )
                print('Money', self.broker.getvalue())
            elif order.issell():
                self.log(
                    f'SELL EXECUTED, Price: {order.executed.price}, ' +
                    f'Cost: {order.executed.value}, ' +
                    f'Comm: {order.executed.comm}'
                )
                print('Money', self.broker.getvalue())

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(
            f'OPERATION PROFIT, GROSS {trade.pnl}, ' +
            f'NET {trade.pnlcomm}'
        )
        print()


    def next(self):
        # Simply log the closing price of the series from the reference

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            if self.rsi_60min[0] >= 70 and self.dataclose[0] > self.bolinger.top[0]:
                # Open SHORT
                self.log('SELL OPENED, %.2f' % self.dataclose[0])
                self.order = self.sell()
            elif self.rsi_60min[0] <= 30 and self.dataclose[0] < self.bolinger.bot[0]:
                # Open LONG
                self.log('BUY OPENED, %.2f' % self.dataclose[0])
                self.order = self.buy()

        else:

            if self.position.size < 0:

                if (
                    (self.position.price - self.dataclose[0]) /
                    self.position.price >= TAKE_PROFIT_THRESH
                ) or (
                    (self.position.price - self.dataclose[0]) /
                    self.position.price < -STOP_LOSS_THRESH
                ):
                    self.log('SELL CLOSED, %.2f' % self.dataclose[0])
                    # Keep track of the created order to avoid a 2nd order
                    self.order = self.buy()

            elif self.position.size > 0:

                if (
                    (self.dataclose[0] - self.position.price) /
                    self.position.price >= TAKE_PROFIT_THRESH
                ) or (
                    (self.dataclose[0] - self.position.price) /
                    self.position.price < -STOP_LOSS_THRESH
                ):
                    self.log('BUY CLOSED, %.2f' % self.dataclose[0])
                    # Keep track of the created order to avoid a 2nd order
                    self.order = self.sell()

ASSET = argv[1]
PRICES_PATH = '/mnt/tick_prices/' + ASSET + '.csv'

# Conditions for CLOSING positions
TAKE_PROFIT_THRESH = (
    open_close_hour_dif_mean[ASSET] + open_close_hour_dif_std[ASSET]
)
STOP_LOSS_THRESH = (
    open_close_hour_dif_mean[ASSET] + open_close_hour_dif_std[ASSET]
)

STAKE = calculate_trade_size(
    STOP_LOSS_THRESH, ticker_info[ASSET]['close']
)
STAKE = round(STAKE)


# Create a cerebro entity
cerebro = bt.Cerebro()

# Add a strategy
cerebro.addstrategy(TestStrategy)
cerebro.addsizer(bt.sizers.FixedSize, stake=STAKE)

# Create a Data Feed
data = btfeeds.GenericCSVData(
    dataname=PRICES_PATH,
    timeframe=bt.TimeFrame.Ticks,
    nullvalue=0.0,
    datetime=1,
    time=2,
    dtformat='%Y-%m-%d',
    tmformat='%H:%M:%S',
    high=3,
    low=3,
    open=3,
    close=3,
    volume=-1,
    openinterest=-1,
    separator = ','
)

# Add the Data Feed to Cerebro
cerebro.replaydata(data, timeframe=bt.TimeFrame.Minutes, compression=60)
#cerebro.replaydata(data, timeframe=bt.TimeFrame.Minutes, compression=5)

# Set our desired cash start
cerebro.broker.setcash(100000.0)

# Set the commission - 0.1% ... divide by 100 to remove the %
cerebro.broker.setcommission(commission=0.0001)

# Print out the starting conditions
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

# Run over everything
cerebro.run()

# Print out the final result
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
print('--' + ASSET + ' ' + str(cerebro.broker.getvalue()) + '--')
