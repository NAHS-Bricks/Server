from helpers.config import *


brick_state_defaults = {
    'all': {
        'id': None,
        'version': None,
        'features': [],
        'desc': '',
        'last_ts': None,
        'initalized': False
    },
    'temp': {
        'last_temps': {},
        'presicion': 11,
        'delay': 60,
        'delay_increase_wait': 3
    },
    'bat': {
        'last_bat_reading': 0,
        'last_bat_ts': None,
        'bat_charging': False,
        'bat_charging_standby': False
    }
}


def __store_v(brick, value):
    brick['version'] = value


def __store_f(brick, value):
    for feature in [f for f in value if f not in brick['features'] and f in brick_state_defaults]:
        brick.update(brick_state_defaults[feature])
        brick['features'].append(feature)


def __store_t(brick, temps):
    if 'temp' not in brick['features']:
        return
    for sensor, temp in temps:
        storagefile = storagedir + brick['id'] + '_' + sensor + '.csv'
        entryline = str(brick['last_ts']) + ';' + str(temp) + '\n'
        with open(storagefile, 'a') as f:
            f.write(entryline)
        brick['last_temps'][sensor] = temp
    brick['delay_increase_wait'] -= (0 if brick['delay_increase_wait'] <= 0 else 1)


def __store_b(brick, voltage):
    if 'bat' not in brick['features']:
        return
    brick['last_bat_reading'] = voltage
    brick['last_bat_ts'] = brick['last_ts']


def __store_y(brick, bools):
    if 'bat' in brick['features']:
        brick['bat_charging'] = ('c' in bools)
        brick['bat_charging_standby'] = ('s' in bools)
    brick['initalized'] = ('i' in bools)


store = {
    'v': __store_v,
    'f': __store_f,
    't': __store_t,
    'b': __store_b,
    'y': __store_y
}
