import backtrader as bt

class RSIStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.datetime(0)
        print('%s, %s' % (dt, txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.dataopen_1min = self.datas[0].open
        self.dataopen_5min = self.datas[1].open

        # To keep track of pending orders
        self.order = None
        # Indicators
        self.rsi_1min = bt.indicators.RSI(self.datas[0])
        self.rsi_5min = bt.indicators.RSI(self.datas[1])


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
        '''with open('../data/' + ASSET + '/log.csv', 'a') as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    self.datas[0].datetime.datetime(0), trade.pnl,
                    trade.pnlcomm, self.broker.getvalue()
                ]
            )'''
        print()


    def next(self):
        # Simply log the closing price of the series from the reference
        #self.log('Close, %.2f' % self.dataclose[0])
        #print(self.dataopen_hour[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            if self.rsi_1min[0] >= 80 and self.rsi_5min[0] >= 80:
                # Open SHORT
                #self.log('SELL OPENED, %.2f' % self.dataclose[0])
                self.order = self.sell()
            elif self.rsi_1min[0] <= 20 and self.rsi_5min[0] <= 20:
                # Open LONG
                #self.log('BUY OPENED, %.2f' % self.dataclose[0])
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
                    #self.log('SELL CLOSED, %.2f' % self.dataclose[0])
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
                    #self.log('BUY CLOSED, %.2f' % self.dataclose[0])
                    # Keep track of the created order to avoid a 2nd order
                    self.order = self.sell()