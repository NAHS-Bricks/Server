from helpers.mongodb import brick_get, brick_save, brick_delete, brick_all_ids, temp_sensor_delete, temp_sensor_get, temp_sensor_save, latch_get, latch_save, latch_delete as mongo_latch_delete
from helpers.influxdb import temp_delete, bat_level_delete, latch_delete as influx_latch_delete
from helpers.feature_versioning import features_available


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
    else:
        return {'s': 14, 'm': 'no object given for setting desc'}
    return {}


def __set_state_desc(data):
    if 'state' not in data:
        return {'s': 15, 'm': 'state is missing in data'}
    if 'latch' not in data:
        return {'s': 13, 'm': 'latch is missing in data'}
    if data['state'] not in range(0, 6):
        return {'s': 7, 'm': 'invalid state range(0, 5)'}
    brick_id, latch_id = data['latch'].split('_')
    latch = latch_get(brick_id, latch_id)
    latch['states_desc'][data['state']] = data['value']
    latch_save(latch)
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
        brick_id, latch_id = data['latch'].split('_')
        latch = latch_get(brick_id, latch_id)
        if data['value'] not in latch['disables']:
            latch['disables'].append(data['value'])
            latch_save(latch)
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
        brick_id, latch_id = data['latch'].split('_')
        latch = latch_get(brick_id, latch_id)
        if data['value'] in latch['disables']:
            latch['disables'].remove(data['value'])
            latch_save(latch)
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
    'del_trigger': __set_del_trigger
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
        if 'brick' in data or 'latch' in data:
            if 'latch' in data:
                brick = brick_get(data['latch'].split('_')[0])
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


def __cmd_get_features(data):
    features = features_available()
    features.remove('all')
    features.remove('os')
    return {'features': features}


admin_commands = {
    'get_bricks': __cmd_get_bricks,
    'get_brick': __cmd_get_brick,
    'set': __cmd_set,
    'delete_brick': __cmd_delete_brick,
    'get_temp_sensor': __cmd_get_temp_sensor,
    'get_latch': __cmd_get_latch,
    'get_features': __cmd_get_features
}
