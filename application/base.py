from enum import Enum
from dataclasses import dataclass


class TradeMode(Enum):
    SELF_USE = 'self_use'
    MARKET = 'market'
    FROM_EXTERNAL = 'from_external'
    TO_ESS = 'to_ess'


@dataclass(frozen=True)
class Trade:
    amount: float
    price: float
    supplier_id: str = 0
    supplier_device_id: str = 0
    consumer_id: str = 0
    consumer_device_id: str = 0
    mode: TradeMode = TradeMode.MARKET

    def refresh_amount(self, new_value):
        return Trade(
            amount=new_value,
            price=self.price,
            supplier_id=self.supplier_id,
            supplier_device_id=self.supplier_device_id,
            consumer_id=self.consumer_id,
            consumer_device_id=self.consumer_device_id,
            mode=self.mode
        )

    def to_json(self):
        return {
            'supplier_id': self.supplier_id,
            'supplier_device_id': self.supplier_device_id,
            'consumer_id': self.consumer_id,
            'consumer_device_id': self.consumer_device_id,
            'amount': self.amount,
            'price': self.price,
            'mode': self.mode.name
        }


class MarketInformation:
    def __init__(self):
        self.prices = []
        self.amount = []
        self.supply_demand_ratio = None
        self.external_price_hour = 0
        self.external_price_day = None
        self.trade_list = []
        self.round_number = 1
        self.last = False
