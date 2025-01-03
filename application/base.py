from dataclasses import dataclass


@dataclass(frozen=True)
class Trade:
    amount: float
    price: float
    supplier_id: str = 0
    supplier_device_id: str = 0
    consumer_id: str = 0
    consumer_device_id: str = 0

    def refresh_amount(self, new_value):
        return Trade(
            amount=new_value,
            price=self.price,
            supplier_id=self.supplier_id,
            supplier_device_id=self.supplier_device_id,
            consumer_id=self.consumer_id,
            consumer_device_id=self.consumer_device_id
        )


class MarketInformation:
    def __init__(self):
        self.supply = {}
        self.demand = {}
        self.external_price = 0
        self.trade_list = []
        self.last = False
