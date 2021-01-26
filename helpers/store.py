from helpers.mongodb import temp_sensor_get, temp_sensor_save
from helpers.shared import brick_state_defaults


def __store_v(brick, versions):
    for feature, version in versions:
        brick['version'][feature] = version


def __store_f(brick, value):
    for feature in [f for f in value if f not in brick['features'] and f in brick_state_defaults]:
        brick.update(brick_state_defaults[feature])
        brick['features'].append(feature)
        if feature not in brick['version']:
            brick['version'][feature] = 0


def __store_t(brick, temps):
    if 'temp' not in brick['features']:
        return
    for sensor_id, temp in temps:
        sensor = temp_sensor_get(sensor_id)
        sensor['prev_reading'] = sensor['last_reading']
        sensor['last_reading'] = temp
        if sensor_id not in brick['temp_sensors']:
            brick['temp_sensors'].append(sensor_id)
        temp_sensor_save(sensor)


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
    for sensor, corr in [(temp_sensor_get(s), c) for s, c in corrs]:
        sensor['corr'] = corr
        temp_sensor_save(sensor)


def __store_x(brick, brick_type):
    brick['type'] = brick_type


def __store_p(brick, precision):
    brick['temp_precision'] = precision


def __store_l(brick, states):
    brick['latch_states'] = states


store = {
    'v': __store_v,
    'f': __store_f,
    't': __store_t,
    'b': __store_b,
    'y': __store_y,
    'c': __store_c,
    'x': __store_x,
    'p': __store_p,
    'l': __store_l
}
