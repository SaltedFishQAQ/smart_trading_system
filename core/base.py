from enum import IntEnum


class Schedule:
    def __init__(self, weekday=0, hour=0):
        self._weekday = weekday
        self._hour = hour

    @property
    def weekday(self):
        return self._weekday

    @property
    def hour(self):
        return self._hour

    def next(self):
        if self.has_next() is False:
            return
        self._hour += 1
        self._weekday += self._hour // 24
        self._hour = self._hour % 24

        return self

    def pre(self):
        if self.has_pre() is False:
            return
        self._hour -= 1
        self._weekday += self._hour // 24
        self._hour = self._hour % 24

        return self

    def has_next(self):
        if self._weekday < 6 or self._hour < 23:
            return True
        return False

    def has_pre(self):
        if self._weekday > 0 or self._hour > 0:
            return True
        return False

    def copy(self):
        return Schedule(self._weekday, self._hour)


class EnergyMode(IntEnum):
    Producer = 1
    Consumer = 1 << 1


class Energy:
    def __init__(self):
        self._energy = None
        self._demand = None

    def charge(self, datetime: Schedule, amount):
        pass

    def discharge(self, datetime: Schedule, amount):
        pass

    def energy_mode(self):
        return 0


