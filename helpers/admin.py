from helpers.mongodb import brick_get, brick_save, brick_all_ids


def __set_desc(brick, data):
    brick['desc'] = data['value']
    return {}


def __set_temp_precision(brick, data):
    if 'temp' not in brick['features']:
        return {'s': 6, 'm': 'temp not in features of brick'}
    if data['value'] not in range(9, 13):
        return {'s': 7, 'm': 'invalid value range(9, 12)'}
    brick['temp_precision'] = data['value']
    brick['admin_override'][data['key']] = True
    return {}


def __set_default(brick, data):
    brick['admin_override'][data['key']] = data['value']
    return {}


_set_direct = {
    'desc': __set_desc
}


_set_indirect = {
    'temp_precision': __set_temp_precision
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
    brick = brick_get(data['brick'])
    if data['key'] in _set_direct:
        result.update(_set_direct[data['key']](brick, data))
    else:
        if 'admin_override' not in brick['features']:
            brick['features'].append('admin_override')
        if 'admin_override' not in brick:
            brick['admin_override'] = {}

        if data['key'] in _set_indirect:
            result.update(_set_indirect[data['key']](brick, data))
        else:
            result.update(__set_default(brick, data))

    brick_save(brick)
    return result


admin_commands = {
    'get_bricks': __cmd_get_bricks,
    'get_brick': __cmd_get_brick,
    'set': __cmd_set
}
