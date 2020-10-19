from helpers.shared import config, send_telegram
import helpers.shared
import os


brick_state_defaults = {
    'all': {
        'id': None,
        'type': None,
        'version': None,
        'features': [],
        'desc': '',
        'last_ts': None,
        'initalized': False
    },
    'temp': {
        'temp_sensors': [],
        'temp_precision': 11,
        'temp_max_diff': 0
    },
    'bat': {
        'bat_last_reading': 0,
        'bat_last_ts': None,
        'bat_charging': False,
        'bat_charging_standby': False,
        'bat_periodic_voltage_request': 10
    },
    'sleep': {
        'sleep_delay': 60,
        'sleep_increase_wait': 3
    }
}

temp_sensor_defaults = {
    'desc': '',
    'last_reading': None,
    'prev_reading': None,
    'corr': None
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
        storagefile = os.path.join(config['storagedir'], config['temp_sensor_dir'], sensor + '.csv')
        entryline = str(brick['last_ts']) + ';' + str(temp) + '\n'
        with open(storagefile, 'a') as f:
            f.write(entryline)
        if sensor not in helpers.shared.temp_sensors:
            helpers.shared.temp_sensors[sensor] = {}
            helpers.shared.temp_sensors[sensor].update(temp_sensor_defaults)
        helpers.shared.temp_sensors[sensor]['prev_reading'] = helpers.shared.temp_sensors[sensor]['last_reading']
        helpers.shared.temp_sensors[sensor]['last_reading'] = temp
        if sensor not in brick['temp_sensors']:
            brick['temp_sensors'].append(sensor)


def __store_b(brick, voltage):
    if 'bat' not in brick['features']:
        return
    brick['bat_last_reading'] = voltage
    brick['bat_last_ts'] = brick['last_ts']


def __store_y(brick, bools):
    if 'bat' in brick['features']:
        brick['bat_charging'] = ('c' in bools)
        brick['bat_charging_standby'] = ('s' in bools)
    brick['initalized'] = ('i' in bools)


def __store_c(brick, corrs):
    for sensor, corr in [(s, c) for s, c in corrs if s in helpers.shared.temp_sensors]:
        helpers.shared.temp_sensors[sensor]['corr'] = corr


def __store_x(brick, brick_type):
    brick['type'] = brick_type


store = {
    'v': __store_v,
    'f': __store_f,
    't': __store_t,
    'b': __store_b,
    'y': __store_y,
    'c': __store_c,
    'x': __store_x
}