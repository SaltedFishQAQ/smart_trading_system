from core.base import Schedule
from core.device import Device
from application.base import Trade
from application.base import MarketInformation


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

    def get_supply(self, datetime: Schedule) -> list[Trade]:
        # TODO: prices decision
        price = 30
        supply_list = []
        for device in self.device_list:
            amount = device.supply(datetime)
            if amount == 0:
                continue
            supply_list.append(Trade(
                supplier_id=self.user_id,
                supplier_device_id=device.device_id,
                price=price,
                amount=amount))

        return supply_list

    def get_demand(self, datetime: Schedule) -> list[Trade]:
        # TODO: prices decision
        price = 30
        demand_list = []
        for device in self.device_list:
            amount = device.demand(datetime)
            if amount == 0:
                continue
            demand_list.append(Trade(
                consumer_id=self.user_id,
                consumer_device_id=device.device_id,
                price=price,
                amount=amount))

        return demand_list
