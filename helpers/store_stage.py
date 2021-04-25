from helpers.mongodb import temp_sensor_get, temp_sensor_save, latch_get, latch_save
from helpers.feature_versioning import feature_update
import copy


def __store_v(brick, versions):
    for feature, version in versions:
        if feature not in brick['features']:
            brick['features'][feature] = 0
        feature_update(brick, feature, brick['features'][feature], version)
        brick['features'][feature] = version


def __store_t(brick, temps):
    if 'temp' not in brick['features']:  # pragma: no cover
        return
    for sensor_id, temp in temps:
        sensor = temp_sensor_get(sensor_id)
        sensor['prev_reading'] = sensor['last_reading']
        sensor['last_reading'] = temp
        if sensor_id not in brick['temp_sensors']:
            brick['temp_sensors'].append(sensor_id)
        temp_sensor_save(sensor)


def __store_b(brick, voltage):
    if 'bat' not in brick['features']:  # pragma: no cover
        return
    brick['bat_last_reading'] = voltage
    brick['bat_last_ts'] = brick['last_ts']


def __store_y(brick, bools):
    if 'bat' in brick['features']:
        brick['bat_charging'] = ('c' in bools)
        brick['bat_charging_standby'] = ('s' in bools)
    brick['initalized'] = ('i' in bools)


def __store_c(brick, corrs):
    if 'temp' not in brick['features']:  # pragma: no cover
        return
    for sensor, corr in [(temp_sensor_get(s), c) for s, c in corrs]:
        sensor['corr'] = corr
        if sensor['_id'] not in brick['temp_sensors']:
            brick['temp_sensors'].append(sensor['_id'])
        temp_sensor_save(sensor)


def __store_x(brick, brick_type):
    brick['type'] = brick_type


def __store_p(brick, precision):
    brick['temp_precision'] = precision


def __store_l(brick, states):
    for i in range(0, len(states)):
        latch = latch_get(brick['_id'], i)
        latch['prev_state'] = latch['last_state']
        latch['prev_ts'] = latch['last_ts']
        latch['last_state'] = states[i]
        latch['last_ts'] = brick['last_ts']
        latch_save(latch)
    brick['latch_count'] = len(states)


store = {
    'v': __store_v,
    't': __store_t,
    'b': __store_b,
    'y': __store_y,
    'c': __store_c,
    'x': __store_x,
    'p': __store_p,
    'l': __store_l
}
