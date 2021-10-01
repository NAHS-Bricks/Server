from connector.mongodb import temp_sensor_get, temp_sensor_save, latch_get, latch_save, signal_all, signal_get, signal_save, signal_delete
from connector.mongodb import humid_get, humid_save
from helpers.feature_versioning import feature_update
import copy


def __store_v(brick, versions):
    tmp_feature_list = list()
    for feature, version in versions:
        tmp_feature_list.append(feature)
        if feature not in brick['features']:
            brick['features'][feature] = -1
        feature_update(brick, feature, brick['features'][feature], version)
        brick['features'][feature] = version

    # remove all features from brick, that hove not been submitted
    for feature in [feature for feature in brick['features'].keys() if feature not in tmp_feature_list]:
        brick['features'].pop(feature, None)


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


def __store_h(brick, humids):
    if 'humid' not in brick['features']:  # pragma: no cover
        return
    for sensor_id, humid in humids:
        sensor = humid_get(sensor_id)
        sensor['prev_reading'] = sensor['last_reading']
        sensor['prev_ts'] = sensor['last_ts']
        sensor['last_reading'] = humid
        sensor['last_ts'] = brick['last_ts']
        if sensor_id not in brick['humid_sensors']:
            brick['humid_sensors'].append(sensor_id)
        humid_save(sensor)


def __store_b(brick, voltage):
    if 'bat' not in brick['features']:  # pragma: no cover
        return
    brick['bat_last_reading'] = voltage
    brick['bat_last_ts'] = brick['last_ts']
    if brick['bat_init_ts'] is None or brick['bat_init_voltage'] <= voltage:
        brick['bat_init_ts'] = brick['last_ts']
        brick['bat_init_voltage'] = voltage


def __store_y(brick, bools):
    if 'bat' in brick['features']:
        brick['bat_charging'] = ('c' in bools)
        brick['bat_charging_standby'] = ('s' in bools)
    brick['initalized'] = ('i' in bools)
    if brick['features']['all'] >= 1.02:
        brick['delay_overwrite'] = ('d' in bools)
    if 'sleep' in brick['features'] and brick['features']['sleep'] >= 1.01:
        brick['sleep_disabled'] = ('q' in bools)
        if brick['sleep_set_disabled'] is None:
            brick['sleep_set_disabled'] = brick['sleep_disabled']


def __store_c(brick, corrs):
    if 'temp' not in brick['features']:  # pragma: no cover
        return
    for sensor, corr in [(temp_sensor_get(s), c) for s, c in corrs]:
        sensor['corr'] = corr
        if sensor['_id'] not in brick['temp_sensors']:
            brick['temp_sensors'].append(sensor['_id'])
        temp_sensor_save(sensor)


def __store_k(brick, corrs):
    if 'humid' not in brick['features']:  # pragma: no cover
        return
    for sensor, corr in [(humid_get(s), c) for s, c in corrs]:
        sensor['corr'] = corr
        if sensor['_id'] not in brick['humid_sensors']:
            brick['humid_sensors'].append(sensor['_id'])
        humid_save(sensor)


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


def __store_s(brick, scount):
    if 'signal' not in brick['features']:  # pragma: no cover
        return
    brick['signal_count'] = scount
    dbcount = 0
    for signal in signal_all(brick['_id']):
        if int(signal['_id'].split('_')[-1]) >= scount:
            signal_delete(signal)
        else:
            dbcount += 1
    if dbcount < scount:
        for i in range(0, scount):
            signal = signal_get(brick['_id'], i)
            signal_save(signal)


def __store_d(brick, default_delay):
    if not brick['features']['all'] >= 1.02:  # pragma: no cover
        return
    brick['delay_default'] = int(default_delay)


store = {
    'v': __store_v,
    't': __store_t,
    'h': __store_h,
    'b': __store_b,
    'y': __store_y,
    'c': __store_c,
    'k': __store_k,
    'x': __store_x,
    'p': __store_p,
    'l': __store_l,
    's': __store_s,
    'd': __store_d
}


def store_exec(brick, delivered_data):
    [store[k](brick, delivered_data[k]) for k in delivered_data if k in store]
