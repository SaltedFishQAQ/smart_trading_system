from utils.printer import Printer
from core.device import Device, DeviceMode
from core.base import EnergyMode, Schedule
from application.base import Trade
from core.external_power_grid import ExternalPowerGrid


class ESS(Device):  # Energy storage system
    def __init__(self, cap):
        super().__init__('ESS', 'energy storage system')
        self._cap = cap
        self._energy = cap*0.5

    def supply(self, _):
        return self._energy

    def charge(self, _, amount):
        self._energy = min(self._energy + amount, self._cap)  # no more than capacity

    def discharge(self, _, amount):
        diff = min(amount, self._energy)  # no less than 0
        self._energy -= diff

        return diff

    def mode(self):
        return DeviceMode.PERSIST

    def energy_mode(self):
        return EnergyMode.Producer | EnergyMode.Consumer


class PCC:  # Point of common coupling
    def __init__(self, name, external):
        self._name = name
        self._external = external
        self._record = []

    def exchange(self, amount):
        if amount < 0:
            return 0
        demand = self._external.allocate(self._name, amount)
        self._record.append(demand)
        return demand


class Microgrids:
    def __init__(self, name):
        self.name = name
        self._ess = ESS(100000)
        self.ess_id = self._ess.device_id
        self.external = ExternalPowerGrid()
        self.external_pcc = PCC(name, self.external)
        self.DERs = {}  # distributed energy resources
        self.consumers = {}
        self.register(self._ess)
        self.printer = Printer()

    def register(self, device: Device):
        if device.energy_mode() & EnergyMode.Producer == EnergyMode.Producer:
            self.DERs[device.device_id] = device
        if device.energy_mode() & EnergyMode.Consumer == EnergyMode.Consumer:
            self.consumers[device.device_id] = device

    def power_flow(self, trade: Trade, datetime: Schedule):
        src_id = trade.supplier_device_id
        dst_id = trade.consumer_device_id
        amount = trade.amount

        if dst_id not in self.consumers:
            return 'device not found'
        consumer = self.consumers[dst_id]

        if src_id in self.DERs:
            producer = self.DERs[src_id]
            flow = producer.discharge(datetime, amount)
        elif src_id == self.external.name:
            flow = self.external.allocate(self.name, amount, datetime)
        else:
            return 'device not found'
        consumer.charge(datetime, flow)
        data = trade.to_json()
        data['datetime'] = f'{datetime.weekday}:{datetime.hour}'
        self.printer.add_data(data)
        # power from src to dst
        print(f'[{trade.mode.name}] {src_id} provide {flow} units of electricity energy to {dst_id}')

    def get_supply(self, datetime: Schedule) -> list[dict]:
        supply_list = [{
                'amount': self._ess.supply(datetime),
                'price': self.external.curr_price(datetime) * 0.9,
                'supplier_id': self.name,
                'supplier_device_id': self.ess_id
            },
            {
                'amount': self.external.supply(datetime),
                'price': self.external.curr_price(datetime),
                'supplier_id': self.external.name,
                'supplier_device_id': self.external.name
            }]

        return supply_list

    def print_flow(self, datetime: Schedule):
        self.printer.print_by_datetime_and_user(f'{datetime.weekday}:{datetime.hour}')

    def print_by_mode(self):
        self.printer.print_by_mode()

    def print_into_excel(self):
        self.printer.print_into_excel()
