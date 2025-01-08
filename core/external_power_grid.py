import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from core.base import Schedule
from collections import defaultdict


startData = '23/12/2024'


class ExternalPowerGrid:
    def __init__(self):
        self.name = 'MainGrid'
        self._prices = None
        self._history_prices = None
        self._bill = defaultdict(float)
        self.init()

    def init(self):
        if self._prices is None:
            # Data source: https://www.mercatoelettrico.org/en-us/Home/Results/Electricity/MGP/Results/ZonalPrices
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external_prices.xlsx')
            df = pd.read_excel(file_path).sort_values(by=['Date', 'Hour'])
            self._prices = []
            self._history_prices = []
            for date, group in df.groupby('Date'):
                date_prices = group['€/MWh'].tolist()  # price unit: €/MWh
                self._history_prices.append(date_prices)
                if date >= startData:
                    self._prices.append(date_prices)

    def curr_price(self, datetime: Schedule) -> float:
        weekday = datetime.weekday
        hour = datetime.hour
        return self._prices[weekday][hour]

    @staticmethod
    def supply(_):
        return sys.float_info.max

    def allocate(self, target, demand, datetime: Schedule):
        self._bill[target] += demand * self.curr_price(datetime)
        return demand

    def get_history_data(self, datetime: Schedule):
        weekday = datetime.weekday + 14
        data_list = []
        for daily in self._history_prices[:weekday]:
            data_list.extend(daily)
        data_list.extend(self._history_prices[weekday][:datetime.hour+1])
        return data_list

    def compare_prices(self, datetime: Schedule, predict):
        test = True
        if test:
            return
        actual = self._prices[datetime.weekday]
        plt.plot(np.arange(len(actual)), actual, label='Actual')
        plt.plot(np.arange(len(predict)), predict, label='Predict', color='red')
        plt.legend()
        plt.show()
