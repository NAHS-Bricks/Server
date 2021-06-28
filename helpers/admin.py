from helpers.mongodb import brick_exists, brick_get, brick_save, brick_delete, brick_all_ids, brick_count
from helpers.mongodb import temp_sensor_exists, temp_sensor_delete, temp_sensor_get, temp_sensor_save, temp_sensor_count
from helpers.mongodb import latch_exists, latch_get, latch_save, latch_delete as mongo_latch_delete, latch_count
from helpers.mongodb import signal_exists, signal_all, signal_delete, signal_count, signal_get, signal_save
from helpers.influxdb import temp_delete, bat_level_delete, latch_delete as influx_latch_delete
from helpers.feature_versioning import features_available
from helpers.current_version import current_brickserver_version
import time


def __set_desc(data):
    if 'brick' in data:
        brick = brick_get(data['brick'])
        brick['desc'] = data['value']
        brick_save(brick)
    elif 'temp_sensor' in data:
        sensor = temp_sensor_get(data['temp_sensor'])
        sensor['desc'] = data['value']
        temp_sensor_save(sensor)
    elif 'latch' in data:
        brick_id, latch_id = data['latch'].split('_')
        latch = latch_get(brick_id, latch_id)
        latch['desc'] = data['value']
        latch_save(latch)
    elif 'signal' in data:
        brick_id, signal_id = data['signal'].split('_')
        signal = signal_get(brick_id, signal_id)
        signal['desc'] = data['value']
        signal_save(signal)
    else:
        return {'s': 14, 'm': 'no object given for setting desc'}
    return {}


def __set_state_desc(data):
    if 'state' not in data:
        return {'s': 15, 'm': 'state is missing in data'}
    if 'latch' in data:
        if data['state'] not in range(0, 6):
            return {'s': 7, 'm': 'invalid state range(0, 5)'}
        latch = latch_get(*data['latch'].split('_'))
        latch['states_desc'][data['state']] = data['value']
        latch_save(latch)
    elif 'signal' in data:
        signal = signal_get(*data['signal'].split('_'))
        if data['state'] not in range(0, len(signal['states_desc'])):
            return {'s': 7, 'm': 'invalid state range(0, ' + str(len(signal['states_desc']) - 1) + ')'}
        signal['states_desc'][data['state']] = data['value']
        signal_save(signal)
    else:
        return {'s': 14, 'm': 'no object given for setting state_desc'}
    return {}


def __set_add_disable(data):
    valid_values = ['metric', 'ui']
    if data['value'] not in valid_values:
        return {'s': 7, 'm': 'invalid value needs to be one of: ' + str(valid_values)}
    if 'temp_sensor' in data:
        sensor = temp_sensor_get(data['temp_sensor'])
        if data['value'] not in sensor['disables']:
            sensor['disables'].append(data['value'])
            temp_sensor_save(sensor)
    elif 'latch' in data:
        latch = latch_get(*data['latch'].split('_'))
        if data['value'] not in latch['disables']:
            latch['disables'].append(data['value'])
            latch_save(latch)
    elif 'signal' in data:
        signal = signal_get(*data['signal'].split('_'))
        if data['value'] not in signal['disables']:
            signal['disables'].append(data['value'])
            signal_save(signal)
    else:
        return {'s': 14, 'm': 'no object given for adding disable'}
    return {}


def __set_del_disable(data):
    valid_values = ['metric', 'ui']
    if data['value'] not in valid_values:
        return {'s': 7, 'm': 'invalid value needs to be one of: ' + str(valid_values)}
    if 'temp_sensor' in data:
        sensor = temp_sensor_get(data['temp_sensor'])
        if data['value'] in sensor['disables']:
            sensor['disables'].remove(data['value'])
            temp_sensor_save(sensor)
    elif 'latch' in data:
        latch = latch_get(*data['latch'].split('_'))
        if data['value'] in latch['disables']:
            latch['disables'].remove(data['value'])
            latch_save(latch)
    elif 'signal' in data:
        signal = signal_get(*data['signal'].split('_'))
        if data['value'] in signal['disables']:
            signal['disables'].remove(data['value'])
            signal_save(signal)
    else:
        return {'s': 14, 'm': 'no object given for deleteing disable'}
    return {}


def __set_temp_precision(data):
    if 'brick' not in data:
        return {'s': 11, 'm': 'brick is missing in data'}
    brick = brick_get(data['brick'])
    if 'temp' not in brick['features']:
        return {'s': 6, 'm': 'temp not in features of brick'}
    if data['value'] not in range(9, 13):
        return {'s': 7, 'm': 'invalid value range(9, 12)'}
    brick['temp_precision'] = data['value']
    brick['admin_override'][data['key']] = True
    brick_save(brick)
    return {}


def __set_add_trigger(data):
    if 'latch' not in data:
        return {'s': 13, 'm': 'latch is missing in data'}
    brick_id, latch_id = data['latch'].split('_')
    brick = brick_get(brick_id)
    if 'latch' not in brick['features']:
        return {'s': 10, 'm': 'latch not in features of brick'}
    if int(data['value']) not in range(0, 4):
        return {'s': 7, 'm': 'invalid value range(0, 3)'}
    brick['admin_override']['latch_triggers'] = True
    latch = latch_get(brick_id, latch_id)
    if int(data['value']) not in latch['triggers']:
        latch['triggers'].append(int(data['value']))
    latch_save(latch)
    brick_save(brick)
    return {}


def __set_del_trigger(data):
    if 'latch' not in data:
        return {'s': 13, 'm': 'latch is missing in data'}
    brick_id, latch_id = data['latch'].split('_')
    brick = brick_get(brick_id)
    if 'latch' not in brick['features']:
        return {'s': 10, 'm': 'latch not in features of brick'}
    if int(data['value']) not in range(0, 4):
        return {'s': 7, 'm': 'invalid value range(0, 3)'}
    brick['admin_override']['latch_triggers'] = True
    latch = latch_get(brick_id, latch_id)
    if int(data['value']) in latch['triggers']:
        latch['triggers'].remove(int(data['value']))
    latch_save(latch)
    brick_save(brick)
    return {}


def __set_signal(data):
    if 'signal' not in data:
        return {'s': 18, 'm': 'signal is missing in data'}
    brick_id, signal_id = data['signal'].split('_')
    brick = brick_get(brick_id)
    if 'signal' not in brick['features']:
        return {'s': 19, 'm': 'signal not in features of brick'}
    signal = signal_get(brick_id, signal_id)
    if int(data['value']) not in range(0, len(signal['states_desc'])):
        return {'s': 7, 'm': 'invalid value range(0, ' + str(len(signal['states_desc']) - 1) + ')'}
    brick['admin_override']['signal_states'] = True
    signal['state'] = int(data['value'])
    signal['state_set_ts'] = int(time.time())
    signal['state_transmitted_ts'] = None
    signal_save(signal)
    brick_save(brick)
    return {}


def __set_default(data):
    if 'brick' not in data:
        return {'s': 11, 'm': 'brick is missing in data'}
    brick = brick_get(data['brick'])
    brick['admin_override'][data['key']] = data['value']
    brick_save(brick)
    return {}


_set_direct = {
    'desc': __set_desc,
    'state_desc': __set_state_desc,
    'add_disable': __set_add_disable,
    'del_disable': __set_del_disable
}


_set_indirect = {
    'temp_precision': __set_temp_precision,
    'add_trigger': __set_add_trigger,
    'del_trigger': __set_del_trigger,
    'signal': __set_signal
}


def __cmd_get_bricks(data):
    return {'bricks': brick_all_ids()}


def __cmd_get_brick(data):
    if 'brick' not in data:
        return {'s': 11, 'm': 'brick is missing in data'}
    return {'brick': brick_get(data['brick'])}


def __cmd_set(data):
    if 'key' not in data:
        return {'s': 4, 'm': 'key to be set is missing in data'}
    if 'value' not in data:
        return {'s': 5, 'm': 'value to be set is missing in data'}

    result = {}
    if data['key'] in _set_direct:
        result.update(_set_direct[data['key']](data))
    else:
        if 'brick' in data or 'latch' in data or 'signal' in data:
            if 'latch' in data:
                brick = brick_get(data['latch'].split('_')[0])
            elif 'signal' in data:
                brick = brick_get(data['signal'].split('_')[0])
            else:
                brick = brick_get(data['brick'])
            if 'admin_override' not in brick['features']:
                brick['features']['admin_override'] = 0
            if 'admin_override' not in brick:
                brick['admin_override'] = {}
            brick_save(brick)

        if data['key'] in _set_indirect:
            result.update(_set_indirect[data['key']](data))
        else:
            result.update(__set_default(data))

    return result


def __cmd_delete_brick(data):
    if 'brick' not in data:
        return {'s': 11, 'm': 'brick is missing in data'}
    brick = brick_get(data['brick'])
    result = {'brick': brick['_id']}
    if 'temp' in brick['features']:
        result['temp_sensors'] = list()
        for sensor in brick['temp_sensors']:
            result['temp_sensors'].append(sensor)
            temp_delete(sensor)
            temp_sensor_delete(sensor)
    if 'latch' in brick['features']:
        result['latches'] = list()
        for i in range(0, brick['latch_count']):
            result['latches'].append(brick['_id'] + '_' + str(i))
            mongo_latch_delete(brick['_id'], i)
            influx_latch_delete(brick['_id'], i)
    if 'signal' in brick['features']:
        result['signals'] = list()
        for signal in signal_all():
            result['signals'].append(signal['_id'])
            signal_delete(signal)
    bat_level_delete(brick['_id'])
    brick_delete(brick['_id'])
    return {'deleted': result}


def __cmd_get_temp_sensor(data):
    if 'temp_sensor' not in data:
        return {'s': 12, 'm': 'temp_sensor is missing in data'}
    return {'temp_sensor': temp_sensor_get(data['temp_sensor'])}


def __cmd_get_latch(data):
    if 'latch' not in data:
        return {'s': 13, 'm': 'latch is missing in data'}
    brick_id, latch_id = data['latch'].split('_')
    return {'latch': latch_get(brick_id, latch_id)}


def __cmd_get_signal(data):
    if 'signal' not in data:
        return {'s': 18, 'm': 'signal is missing in data'}
    brick_id, signal_id = data['signal'].split('_')
    return {'signal': signal_get(brick_id, signal_id)}


def __cmd_get_features(data):
    features = features_available()
    features.remove('all')
    features.remove('os')
    return {'features': features}


def __cmd_get_version(data):
    return {'version': current_brickserver_version}


def __cmd_get_count(data):
    if 'item' not in data:
        return {'s': 16, 'm': 'item is missing in data'}
    valid_items = ['bricks', 'temp_sensors', 'latches', 'signals']
    if data['item'] not in valid_items:
        return {'s': 17, 'm': 'invalid item given. Needs to be one of: ' + str(valid_items)}
    c = 0
    if data['item'] == 'bricks':
        c = brick_count()
    if data['item'] == 'temp_sensors':
        c = temp_sensor_count()
    if data['item'] == 'latches':
        c = latch_count()
    if data['item'] == 'signals':
        c = signal_count()
    return {'count': c}


admin_commands = {
    'get_bricks': __cmd_get_bricks,
    'get_brick': __cmd_get_brick,
    'set': __cmd_set,
    'delete_brick': __cmd_delete_brick,
    'get_temp_sensor': __cmd_get_temp_sensor,
    'get_latch': __cmd_get_latch,
    'get_signal': __cmd_get_signal,
    'get_features': __cmd_get_features,
    'get_version': __cmd_get_version,
    'get_count': __cmd_get_count
}


def admin_interface(data):
    result = {'s': 0}

    if 'command' not in data:
        return {'s': 1, 'm': 'command is missing'}
    if data['command'] not in admin_commands:
        return {'s': 2, 'm': 'unknown command'}
    if 'brick' in data and not brick_exists(data['brick']):
        return {'s': 3, 'm': 'invalid brick'}
    if 'temp_sensor' in data and not temp_sensor_exists(data['temp_sensor']):
        return {'s': 8, 'm': 'invalid temp_sensor'}
    if 'latch' in data:
        brick_id, latch_id = data['latch'].split('_')
        if not latch_exists(brick_id, latch_id):
            return {'s': 9, 'm': 'invalid latch'}
    if 'signal' in data:
        brick_id, signal_id = data['signal'].split('_')
        if not signal_exists(brick_id, signal_id):
            return {'s': 20, 'm': 'invalid signal'}

    result.update(admin_commands[data['command']](data))
    return result
