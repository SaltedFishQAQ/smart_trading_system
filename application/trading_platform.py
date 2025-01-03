import copy
from core.microgrids import Microgrids
from core.base import Schedule
from application.base import Trade
from application.user import User
from application.base import MarketInformation
from core.external_power_grid import ExternalPowerGrid


class DSM:  # Demand side management
    def __init__(self, external: ExternalPowerGrid):
        self._market_information = {}
        self.external = external

    def market_information(self, datetime: Schedule):
        if (datetime.weekday, datetime.hour) in self._market_information:
            return self._market_information[(datetime.weekday, datetime.hour)]

        return self.predict_market(datetime)

    def predict_market(self, datetime: Schedule):
        predict = MarketInformation()
        if datetime.has_pre() and len(self._market_information) > 0:
            # TODO: predict supply and demand
            pre_datetime = datetime.copy().pre()
            predict = self._market_information[(pre_datetime.weekday, pre_datetime.hour)]
        predict.external_price = self.external.curr_price(datetime)

        return predict

    def record_market(self, datetime: Schedule, trade_list: list[Trade]):
        if len(trade_list) == 0:
            return
        data = MarketInformation()
        data.external_price = self.external.curr_price(datetime)
        if (datetime.weekday, datetime.hour) in self._market_information:
            data = self._market_information[(datetime.weekday, datetime.hour)]

        data.trade_list.extend(trade_list)
        for trade in trade_list:
            data.supply[trade.price] = data.supply.get(trade.price, 0) + trade.amount
            data.demand[trade.price] = data.demand.get(trade.price, 0) + trade.amount


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

    def register_user(self, user: User):
        self.users[user.user_id] = user
        for device in user.device_list:
            self.microgrids.register(device)

    def handle(self, datetime: Schedule):
        self.market_manager.predict_market(datetime)  # predicting supply and demand

        round_number = 1
        last_round = False
        supply_list = []
        demand_list = []
        while last_round is False:
            if round_number == 5:
                last_round = True

            self.notify_market(datetime, last_round)  # notify user

            supply_list = self.get_supply_list(datetime)  # collect supply
            demand_list = self.get_demand_list(datetime)  # collect demand
            if len(demand_list) == 0 or len(supply_list) == 0:
                break

            supply_list = sorted(copy.deepcopy(supply_list), key=lambda x: x.price)
            demand_list = sorted(copy.deepcopy(demand_list), key=lambda x: x.price, reverse=True)

            trade_list = self.match_trades(datetime, supply_list, demand_list, last_round)  # trade matching
            self.allocator.distribute_energy(trade_list, datetime)  # distribute energy by trade

            self.market_manager.record_market(datetime, trade_list)  # record trade

            round_number += 1

        self.finishing_touches(datetime, supply_list, demand_list)

    def notify_market(self, datetime: Schedule, last: bool):
        curr_market = self.market_manager.market_information(datetime)
        curr_market.last = last
        for user in self.users.values():
            user.update_market_information(datetime, curr_market)

    def get_supply_list(self, datetime: Schedule):
        result = []
        for user in self.users.values():
            result.extend(user.get_supply(datetime))
        return result

    def get_demand_list(self, datetime: Schedule):
        result = []
        for user in self.users.values():
            result.extend(user.get_demand(datetime))
        return result

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
