import os
from utils.config import ConfigLoader
from core.base import Schedule
from core.device import convert_to_device
from core.microgrids import Microgrids
from application.user import User
from application.trading_platform import TradingPlatform


if __name__ == '__main__':
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'application/device.xml')
    config = ConfigLoader(config_path).json()

    # prepare platform
    microgrids = Microgrids('group8')  # build microgrids
    platform = TradingPlatform(microgrids)  # load platform

    # register user
    for user_id in config['user']:
        devices = config['user'][user_id]
        device_list = []
        for device in devices:
            count = int(config['user'][user_id][device])
            for _ in range(count):
                device_list.append(convert_to_device(config, device))
        platform.register_user(User(user_id, device_list))

    # start
    datetime = Schedule()
    while True:
        print(f'-------- weekday: {datetime.weekday}, hour: {datetime.hour} --------')
        platform.handle(datetime)
        if datetime.has_next() is False:
            break
        datetime.next()

    microgrids.print_into_excel()
