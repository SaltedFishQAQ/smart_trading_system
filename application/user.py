import copy

from core.base import Schedule
from core.device import Device, DeviceMode
from application.base import Trade, TradeMode
from application.base import MarketInformation
from application.algorithms.user import predict_prices


class User:
    def __init__(self, user_id, device_list: list[Device]):
        self.user_id = user_id
        self.device_list = device_list
        self.selling_price_range = (25, 99)
        self.purchase_price_range = (1, 75)
        self._market = {}

    def update_market_information(self, datetime: Schedule, data: MarketInformation):
        self._market[(datetime.weekday, datetime.hour)] = data

    def get_market_information(self, datetime: Schedule):
        return self._market[(datetime.weekday, datetime.hour)]

    def get_supply_demand(self, datetime: Schedule) -> (list[Trade], list[Trade], list[Trade]):
        curr_market = self.get_market_information(datetime)
        index = curr_market.round_number-1
        # get supply and demand
        supply_list = self.get_supply(datetime)
        demand_list = self.get_demand(datetime)
        # calc sell and buy price
        self_supply = 0
        self_demand = 0
        for supply in supply_list:
            self_supply += supply['supply']
        for demand in demand_list:
            self_demand += demand['demand']
        self_ratio = 1
        if self_demand > 0:
            self_ratio = self_supply/self_demand
        sell, buy = predict_prices(curr_market.supply_demand_ratio[index], curr_market.prices[index], self_ratio)
        # determine trade
        trade_self_list = []
        if sell < buy:
            supply_list_cp = copy.deepcopy(supply_list)
            demand_list_cp = copy.deepcopy(demand_list)
            while supply_list_cp and demand_list_cp:
                supply = supply_list_cp[0]
                demand = demand_list_cp[0]
                amount = min(supply['supply'], demand['demand'])
                trade_self_list.append(Trade(
                    supplier_id=self.user_id,
                    supplier_device_id=supply['id'],
                    consumer_id=self.user_id,
                    consumer_device_id=demand['id'],
                    price=sell,
                    amount=amount,
                    mode=TradeMode.SELF_USE
                ))
                if supply['supply'] == amount:
                    supply_list_cp.pop(0)
                else:
                    supply_list_cp[0]['supply'] = supply['supply'] - amount
                if demand['demand'] == amount:
                    demand_list_cp.pop(0)
                else:
                    demand_list_cp[0]['demand'] = demand['demand'] - amount
        trade_supply_list = []
        trade_demand_list = []
        for supply in supply_list:
            trade_supply_list.append(Trade(
                supplier_id=self.user_id,
                supplier_device_id=supply['id'],
                price=sell,
                amount=supply['supply']))
        for demand in demand_list:
            trade_demand_list.append(Trade(
                consumer_id=self.user_id,
                consumer_device_id=demand['id'],
                price=buy,
                amount=demand['demand']))

        return trade_supply_list, trade_demand_list, trade_self_list

    def get_supply(self, datetime: Schedule):
        supply_list = []
        for device in self.device_list:
            amount = device.supply(datetime)
            if amount == 0:
                continue
            supply_list.append({
                'id': device.device_id,
                'supply': device.supply(datetime),
            })

        return supply_list

    def get_demand(self, datetime: Schedule):
        curr_market = self._market[(datetime.weekday, datetime.hour)]
        prices = copy.deepcopy(curr_market.external_price_day[datetime.hour:])
        min_hour = min(range(len(prices)), key=lambda i: prices[i])
        demand_list = []
        for device in self.device_list:
            amount = device.demand(datetime)
            if amount == 0:
                continue
            data = {
                'id': device.device_id,
                'demand': device.demand(datetime),
            }
            if device.mode() == DeviceMode.IMMEDIATE or device.mode() == DeviceMode.PERSIST:
                demand_list.append(data)
            elif min_hour == datetime.hour:
                demand_list.append(data)

        return demand_list
