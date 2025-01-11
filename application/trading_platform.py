import copy
import numpy as np
from core.microgrids import Microgrids
from core.base import Schedule
from application.base import Trade
from application.user import User
from application.base import MarketInformation
from application.algorithms.market import predict_external_price, predict_supply_demand
from core.external_power_grid import ExternalPowerGrid


MAX_ROUND = 5


class DSM:  # Demand side management
    def __init__(self, external: ExternalPowerGrid):
        self._market_information = {}
        self.external = external

    def market_information(self, datetime: Schedule):
        if (datetime.weekday, datetime.hour) not in self._market_information:
            self._market_information[(datetime.weekday, datetime.hour)] = self.predict_market(datetime)

        return self._market_information[(datetime.weekday, datetime.hour)]

    def predict_market(self, datetime: Schedule):
        predict_market = MarketInformation()
        # supply and demand
        if datetime.has_pre() and len(self._market_information) > 0:
            pre_datetime = datetime.copy().pre()
            pre_market = self._market_information[(pre_datetime.weekday, pre_datetime.hour)]
            predict_market.prices = copy.deepcopy(pre_market.prices)
            predict_market.amount = copy.deepcopy(pre_market.amount)
            predict_market.supply_demand_ratio = copy.deepcopy(pre_market.supply_demand_ratio)
        else:
            predict_market.prices = [0] * MAX_ROUND
            predict_market.amount = [0] * MAX_ROUND
            predict_market.supply_demand_ratio = [1] * MAX_ROUND

        # external_price_hour
        predict_market.external_price_hour = self.external.curr_price(datetime)
        # external_price_day = [...history_data, ...predict_data]
        offset = datetime.hour+1
        history_data = self.external.get_history_data(datetime)
        predict_data = predict_external_price(np.arange(1, len(history_data) + 1), history_data, 24 - offset)
        predict_market.external_price_day = np.concatenate((history_data[-offset:], predict_data))
        self.external.compare_prices(datetime, predict_market.external_price_day)

        return predict_market

    def adjust_market(self, datetime: Schedule, round_number):
        curr_market = self.market_information(datetime)
        if datetime.has_pre() and len(self._market_information) > 0:
            pre_datetime = datetime.copy().pre()
            pre_market = self._market_information[(pre_datetime.weekday, pre_datetime.hour)]
            predict_supply_demand(pre_market.supply_demand_ratio, pre_market.prices,
                                  curr_market.supply_demand_ratio, curr_market.prices, round_number)

    def record_market(self, datetime: Schedule, trade_list: list[Trade]):
        if len(trade_list) == 0:
            return
        data = MarketInformation()
        data.external_price_hour = self.external.curr_price(datetime)
        if (datetime.weekday, datetime.hour) in self._market_information:
            data = self._market_information[(datetime.weekday, datetime.hour)]

        data.trade_list.extend(trade_list)
        prices = 0
        amount = 0
        index = data.round_number-1
        if data.last:
            amount = data.amount[index]
            prices = data.prices[index]*amount

        for trade in trade_list:
            prices += trade.price * trade.amount
            amount += trade.amount
        if amount > 0:
            data.prices[index] = prices/amount
            data.amount[index] = amount


class DMS:  # Distribution management systems
    def __init__(self, microgrids: Microgrids):
        self.microgrids = microgrids

    def distribute_energy(self, trade_list: list[Trade], datetime: Schedule):
        for trade in trade_list:
            self.microgrids.power_flow(trade.supplier_device_id, trade.consumer_device_id, datetime, trade.amount)


class TradingPlatform:
    def __init__(self, microgrids: Microgrids):
        self.microgrids = microgrids
        self.market_manager = DSM(self.microgrids.external)
        self.allocator = DMS(microgrids)
        self.users = {}
        self.max_round = MAX_ROUND

    def register_user(self, user: User):
        self.users[user.user_id] = user
        for device in user.device_list:
            self.microgrids.register(device)

    def handle(self, datetime: Schedule):
        round_number = 1
        last_round = False
        supply_list = []
        demand_list = []
        while last_round is False:
            if round_number == self.max_round:
                last_round = True

            self.notify_market(datetime, round_number, last_round)  # notify user

            supply_list, demand_list = self.get_supply_demand_list(datetime)  # collect supply and demand
            if len(demand_list) == 0 or len(supply_list) == 0:
                break

            supply_list = sorted(copy.deepcopy(supply_list), key=lambda x: x.price)
            demand_list = sorted(copy.deepcopy(demand_list), key=lambda x: x.price, reverse=True)

            trade_list = self.match_trades(datetime, supply_list, demand_list, last_round)  # trade matching
            self.allocator.distribute_energy(trade_list, datetime)  # distribute energy by trade
            self.market_manager.record_market(datetime, trade_list)  # record trade

            round_number += 1

        self.finishing_touches(datetime, supply_list, demand_list)

    def notify_market(self, datetime: Schedule, round_number, last: bool):
        curr_market = self.market_manager.market_information(datetime)
        curr_market.round_number = round_number
        curr_market.last = last
        for user in self.users.values():
            user.update_market_information(datetime, curr_market)

    def get_supply_demand_list(self, datetime: Schedule):
        total_supply_list, total_demand_list, total_trade_list = [], [], []
        total_supply = 0
        total_demand = 0
        for user in self.users.values():
            supply_list, demand_list, trade_list = user.get_supply_demand(datetime)
            for supply in supply_list:
                total_supply += supply.amount
            for demand in demand_list:
                total_demand += demand.amount
            total_supply_list.extend(supply_list)
            total_demand_list.extend(demand_list)
            total_trade_list.extend(trade_list)
        self.allocator.distribute_energy(total_trade_list, datetime)  # energy for own use

        curr_market = self.market_manager.market_information(datetime)
        index = curr_market.round_number-1
        if total_supply > 0 and total_demand > 0:
            curr_market.supply_demand_ratio[index] = total_supply/total_demand
        else:
            curr_market.supply_demand_ratio[index] = 0

        return total_supply_list, total_demand_list

    def match_trades(self, datetime: Schedule, supply_list: list[Trade], demand_list: list[Trade], last: bool):
        max_price = self.microgrids.external.curr_price(datetime)

        trade_list = []
        while supply_list and demand_list:
            supply = supply_list[0]
            demand = demand_list[0]
            if supply.price >= max_price:
                break

            amount = min(supply.amount, demand.amount)
            if supply.price <= demand.price:  # trade matching phase
                price = (supply.price + demand.price) / 2
            elif last:  # settlement phase
                price = supply.price
            else:
                break

            trade_list.append(Trade(
                amount=amount,
                price=price,
                supplier_id=supply.supplier_id,
                supplier_device_id=supply.supplier_device_id,
                consumer_id=demand.consumer_id,
                consumer_device_id=demand.consumer_device_id
            ))

            if supply.amount == amount:
                supply_list.pop(0)
            else:
                supply_list[0] = supply.refresh_amount(supply.amount - amount)
            if demand.amount == amount:
                demand_list.pop(0)
            else:
                demand_list[0] = demand.refresh_amount(demand.amount - amount)

        return trade_list

    def finishing_touches(self, datetime: Schedule, supply_list: list[Trade], demand_list: list[Trade]):
        trade_list = []
        for supply in supply_list:
            price = 0
            trade_list.append(Trade(
                amount=supply.amount,
                price=price,
                supplier_id=supply.supplier_id,
                supplier_device_id=supply.supplier_device_id,
                consumer_id=self.microgrids.name,
                consumer_device_id=self.microgrids.ess_id
            ))

        self.allocator.distribute_energy(trade_list, datetime)
        self.market_manager.record_market(datetime, trade_list)

        final_supply_list = self.microgrids.get_supply(datetime)
        index = 0
        while demand_list:
            supply = final_supply_list[index]
            if index == 0 and supply['amount'] == 0:
                index = 1
                continue
            demand = demand_list[0]
            amount = min(supply['amount'], demand.amount)

            trade_list.append(Trade(
                amount=amount,
                price=supply['price'],
                supplier_id=supply['supplier_id'],
                supplier_device_id=supply['supplier_device_id'],
                consumer_id=demand.consumer_id,
                consumer_device_id=demand.consumer_device_id
            ))

            supply['amount'] -= amount
            if demand.amount == amount:
                demand_list.pop(0)
            else:
                demand_list[0] = demand.refresh_amount(demand.amount-amount)

        self.allocator.distribute_energy(trade_list, datetime)
        self.market_manager.record_market(datetime, trade_list)
