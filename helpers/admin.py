from helpers.mongodb import brick_get, brick_save, brick_delete, brick_all_ids, temp_sensor_delete, temp_sensor_get, temp_sensor_save, latch_get, latch_save
from helpers.influxdb import temp_delete, bat_level_delete
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
    return {}


def __set_temp_precision(data):
    if 'brick' in data:
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
    if 'latch' in data:
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
    if 'latch' in data:
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
    if 'brick' in data:
        brick = brick_get(data['brick'])
        brick['admin_override'][data['key']] = data['value']
        brick_save(brick)
    return {}


_set_direct = {
    'desc': __set_desc
}


_set_indirect = {
    'temp_precision': __set_temp_precision,
    'add_trigger': __set_add_trigger,
    'del_trigger': __set_del_trigger
}


def __cmd_get_bricks(data):
    return {'bricks': brick_all_ids()}


def __cmd_get_brick(data):
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
    brick = brick_get(data['brick'])
    result = {'brick': brick['_id']}
    if 'temp' in brick['features']:
        result['temp_sensors'] = []
        for sensor in brick['temp_sensors']:
            result['temp_sensors'].append(sensor)
            temp_delete(sensor)
            temp_sensor_delete(sensor)
    bat_level_delete(brick['_id'])
    brick_delete(brick['_id'])
    return {'deleted': result}


def __cmd_get_temp_sensor(data):
    return {'temp_sensor': temp_sensor_get(data['temp_sensor'])}


def __cmd_get_features(data):
    features = features_available()
    if 'all' in features:
        features.remove('all')
    if 'os' in features:
        features.remove('os')
    return {'features': features}


admin_commands = {
    'get_bricks': __cmd_get_bricks,
    'get_brick': __cmd_get_brick,
    'set': __cmd_set,
    'delete_brick': __cmd_delete_brick,
    'get_temp_sensor': __cmd_get_temp_sensor,
    'get_features': __cmd_get_features
}
