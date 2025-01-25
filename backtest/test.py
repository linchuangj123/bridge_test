import tushare as ts
from datetime import datetime
import pandas as pd
import backtrader as bt

token = "e5ec74d7d341a7f761050dae79d5d342312b74b6faee4914ff39785b"
ts.set_token(token)


def get_data(code, start, end):
    # 导入数据
    df = ts.get_k_data(code, start=start, end=end)
    df.index = pd.to_datetime(df.date)
    df['openinterest'] = 0
    # 读取日期
    df['date'] = df['date'].apply(str)
    df['date'] = pd.to_datetime(df['date'])
    date_list = df['date'].to_list()
    from_date = datetime.strptime(str(date_list[0]), "%Y-%m-%d %H:%M:%S")  # 数据的起始日期
    to_date = datetime.strptime(str(date_list[-1]), "%Y-%m-%d %H:%M:%S")  # 数据的起始日期

    df = df[['open', 'high', 'low', 'close', 'volume', 'openinterest']]
    data = bt.feeds.PandasData(dataname=df, fromdate=from_date, todate=to_date)
    return data


class MyStrategy(bt.Strategy):  # 策略
    params = (('a', 12), ('b', 26),)

    def __init__(self):
        self.order = None
        self.ma1 = bt.indicators.SMA(self.datas[0], period=self.params.a)  # 计算平均线
        self.ma2 = bt.indicators.SMA(self.datas[0], period=self.params.b)  # 计算平均线

    # 计算买股数
    def buy_size(self):
        cash = self.broker.getcash()  # 获取当前剩余金额
        amount = cash * 0.2
        price = self.datas[0].close[0]  # 获取当前股票价格
        size = int(amount / price)
        return size

    def next(self):
        # 判断是否在交易
        if (self.order):
            return
        # 交易策略
        if not self.position:
            if self.ma1[0] > self.ma2[0]:
                size = self.buy_size()
                self.order = self.buy(size=size)
        else:
            if self.ma1[0] < self.ma2[0]:
                self.order = self.sell(size=self.position.size)  # 卖出所有持仓
            else:
                size = self.buy_size()
                self.order = self.buy(size=size)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return  # 订单已提交或接受，无需处理
        if order.status in [order.Completed]:
            self.order = None  # 重置订单状态
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.order = None  # 重置订单状态


data = get_data(code='000001', start='2023-01-01', end='2023-12-31')

cerebro = bt.Cerebro()  # 创建大脑

cerebro.adddata(data)  # 将数据加入回测系统

cerebro.addstrategy(MyStrategy)  # 加入自己的策略

start_cash = 1000000
cerebro.broker.setcash(start_cash)  # 设置金额

slippage = 0.0001
cerebro.broker.set_slippage_perc(slippage)  # 设置滑点（利息）

# 执行回测
print(f"初始资金:{start_cash}")
cerebro.run()
end_cash = cerebro.broker.getvalue()
rate = (end_cash - start_cash) / start_cash * 100
print(f"收益率:{rate}%")
print(f"剩余总资金:{end_cash}")
