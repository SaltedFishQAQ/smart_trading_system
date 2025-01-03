import sys
from core.base import Schedule
from collections import defaultdict

# Data source: https://www.mercatoelettrico.org/en-us/Home/Results/Electricity/MGP/Results/ZonalPrices
# price:€/MWh
electricity_prices = {
    '23/12/2024': [51.12, 30.54, 10.19, 7.33, 6.00, 51.03, 99.99, 128.60, 141.19, 122.80, 112.07, 103.61, 100.00,
                   101.40, 108.02, 114.85, 123.00, 128.56, 124.87, 127.77, 119.10, 109.28, 105.82, 105.49],
    '24/12/2024': [86.03, 82.84, 81.89, 78.00, 78.78, 80.60, 108.86, 155.00, 170.00, 157.37, 120.00, 118.16, 117.49,
                   115.38, 117.98, 139.65, 161.00, 172.75, 173.66, 171.81, 157.71, 141.31, 127.36, 109.90],
    '25/12/2024': [116.03, 105.98, 85.07, 80.81, 75.99, 80.81, 107.85, 121.00, 119.00, 99.24, 93.56, 92.55, 94.41,
                   91.01, 85.08, 97.90, 123.50, 150.00, 158.22, 160.00, 150.99, 138.96, 126.96, 110.80],
    '26/12/2024': [114.39, 105.30, 96.10, 95.67, 90.87, 95.10, 99.00, 115.82, 119.44, 118.23, 113.25, 106.01, 107.71,
                   103.90, 109.64, 120.75, 126.53, 149.98, 155.71, 160.30, 155.28, 146.83, 132.43, 118.27],
    '27/12/2024': [118.61, 113.00, 106.16, 101.76, 99.58, 106.20, 121.00, 140.00, 157.23, 144.06, 123.46, 119.06,
                   118.30, 120.10, 124.40, 144.06, 152.00, 168.21, 168.21, 167.62, 160.59, 149.65, 135.00, 122.11],
    '28/12/2024': [126.40, 116.63, 110.15, 105.92, 102.93, 105.58, 120.10, 127.50, 128.09, 128.30, 122.83, 113.40,
                   108.97, 110.01, 114.09, 130.77, 147.50, 159.77, 165.00, 166.62, 160.59, 149.61, 132.98, 129.16],
    '29/12/2024': [137.74, 129.43, 127.56, 126.07, 125.82, 127.45, 137.74, 156.11, 147.00, 137.74, 124.30, 119.78,
                   123.01, 120.10, 120.89, 138.97, 167.00, 178.42, 176.83, 178.88, 178.89, 170.09, 158.62, 138.00]
}


class ExternalPowerGrid:
    def __init__(self):
        self.name = 'MainGrid'
        self._prices = None
        self._bill = defaultdict(float)
        self.init()

    def init(self):
        if self._prices is None:
            self._prices = []
            for date in electricity_prices:
                self._prices.append(electricity_prices[date])

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
