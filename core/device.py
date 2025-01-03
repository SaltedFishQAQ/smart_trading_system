import uuid
import random
import numpy as np
from enum import Enum
from core.base import Energy, Schedule, EnergyMode


class DeviceMode(Enum):
    ONCE = 'once'  # only execute once, no time limit
    PERSIST = 'persist'  # keep executing
    IMMEDIATE = 'immediate'  # only executed once, but must be executed immediately


class Device(Energy):
    def __init__(self, device_id, device_type):
        super().__init__()
        self.device_id = device_id
        self.device_type = device_type

    def supply(self, datetime: Schedule):
        return 0

    def demand(self, datetime: Schedule):
        return 0

    def mode(self):
        pass


class SolarPanels(Device):
    def __init__(self, device_id):
        super().__init__(device_id, "solar panels")
        self.init()

    def init(self):
        self._energy = np.full((7, 24), 0)
        offset = random.randint(7, 13)
        duration = random.randint(4, 6)
        for daily_energy in self._energy:
            daily_energy[offset:offset+duration] = np.random.randint(240, 270, size=duration)

    def supply(self, datetime: Schedule):
        return self._energy[datetime.weekday, datetime.hour]

    def mode(self):
        return DeviceMode.PERSIST

    def energy_mode(self):
        return EnergyMode.Producer

    def discharge(self, datetime: Schedule, amount):
        diff = min(self._energy[datetime.weekday][datetime.hour], amount)
        self._energy[datetime.weekday][datetime.hour] -= diff

        return diff


class EV(Device):
    def __init__(self, device_id):
        super().__init__(device_id, "electric vehicles")
        self.init()

    def init(self):
        self._demand = random.randint(50*1000, 75*1000) / 0.85

    def demand(self, _):
        return self._demand

    def mode(self):
        return DeviceMode.ONCE

    def energy_mode(self):
        return EnergyMode.Consumer

    def charge(self, datetime: Schedule, amount):
        diff = min(self._demand, amount)
        self._demand -= diff

        return diff


class Appliances(Device):
    def __init__(self, device_id):
        super().__init__(device_id, "appliances")
        self.init()

    def init(self):
        per_cost = random.randint(50, 200)
        self._demand = np.full((7, 24), per_cost)

    def demand(self, datetime: Schedule):
        return self._demand[datetime.weekday][datetime.hour]

    def mode(self):
        return DeviceMode.PERSIST

    def energy_mode(self):
        return EnergyMode.Consumer

    def charge(self, datetime: Schedule, amount):
        diff = min(self._demand, amount)
        self._demand -= diff

        return diff


class Other(Device):
    def __init__(self, device_id, base_demand=20, frequency=168, device_type="other"):
        super().__init__(device_id, device_type)
        self.init(base_demand)
        self.offset = (random.randint(0, 1), random.randint(2, 23))
        self.frequency = frequency

    def init(self, base_demand):
        self._demand = base_demand + random.randint(20, 100)

    def demand(self, datetime: Schedule):
        if datetime.weekday == self.offset[0] and datetime.hour == self.offset[1]:
            return self._demand

        return 0

    def mode(self):
        return DeviceMode.IMMEDIATE

    def energy_mode(self):
        return EnergyMode.Consumer

    def charge(self, datetime: Schedule, amount):
        diff = min(self._demand, amount)
        self._demand -= diff

        if self._demand == 0:
            (weekday, hour) = self.offset
            weekday = (weekday + self.frequency/24) % 7
            hour = (hour + self.frequency % 24) % 24
            self.offset = (weekday, hour)

        return diff


def convert_to_device(config, name):
    device_id = str(uuid.uuid4())[:8]
    if name == 'solar_panels':
        device = SolarPanels(device_id)
    elif name == 'ev':
        device = EV(device_id)
    elif name == 'appliances':
        device = Appliances(device_id)
    else:
        demand, frequency = 20, 24*7
        if name in config:
            demand = int(config[name]['average'])
            frequency = int(config[name]['frequency'])
        device = Other(device_id, demand, frequency, name)

    return device
