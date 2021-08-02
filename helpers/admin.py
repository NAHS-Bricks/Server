from connector.mongodb import brick_exists, brick_get, brick_save, brick_delete, brick_all_ids, brick_count
from connector.mongodb import temp_sensor_exists, temp_sensor_delete, temp_sensor_get, temp_sensor_save, temp_sensor_count
from connector.mongodb import latch_exists, latch_get, latch_save, latch_delete as mongo_latch_delete, latch_count
from connector.mongodb import signal_exists, signal_all, signal_delete, signal_count, signal_get, signal_save
from connector.mongodb import event_get, event_count, event_save, event_all, event_delete, event_exists
from connector.mongodb import event_data_get, event_data_delete, event_data_save, event_data_all, event_data_count
from connector.influxdb import temp_delete, bat_stats_delete, latch_delete as influx_latch_delete
from connector.rabbitmq import event_create
from event.commands import commands as event_commands
from event.reactions import reactions as event_reactions
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


def __set_pos(data):
    if 'event' not in data:
        return {'s': 22, 'm': 'event is missing in data'}
    event = event_get(data['event'])
    if 'reaction_src' in data:
        if data['reaction_src'] not in range(0, len(event['reactions'])):
            return {'s': 7, 'm': f"invalid index range(0, {len(event['reactions']) - 1}) for reaction_src"}
        if data['value'] not in range(0, len(event['reactions'])):
            return {'s': 7, 'm': f"invalid index range(0, {len(event['reactions']) - 1}) for value"}
        reaction = event['reactions'].pop(data['reaction_src'])
        event["reactions"].insert(data['value'], reaction)
        event_save(event)
    else:
        brick = brick_get(event['brick_id'])
        if data['value'] not in range(0, len(brick['events'])):
            return {'s': 7, 'm': f"invalid index range(0, {len(brick['events']) - 1}) for value"}
        brick['events'].remove(event['_id'])
        brick['events'].insert(data['value'], event['_id'])
        brick_save(brick)
    return {}


def __set_event_command(data):
    if 'event_data' not in data:
        return {'s': 24, 'm': 'event_data is missing in data'}
    if data['value'] not in event_commands:
        return {'s': 28, 'm': 'invalid event_command in value'}
    event = event_get(data['event'])
    event['command'] = [data['value'], data['event_data']]
    event_save(event)
    return {}


def __set_bat_solar_charging(data):
    if 'brick' not in data:
        return {'s': 11, 'm': 'brick is missing in data'}
    if not isinstance(data['value'], bool):
        return {'s': 7, 'm': 'invalid value, needs to be a bool'}
    brick = brick_get(data['brick'])
    brick['bat_solar_charging'] = data['value']
    brick_save(brick)
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
    'del_disable': __set_del_disable,
    'pos': __set_pos,
    'event_command': __set_event_command,
    'bat_solar_charging': __set_bat_solar_charging
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
        brick = None
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
            if brick is not None:
                event_create(brick_get(brick['_id']), brick)
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
        for signal in signal_all(brick_id=brick['_id']):
            result['signals'].append(signal['_id'])
            signal_delete(signal)
    for event in brick['events']:
        if 'events' not in result:
            result['events'] = list()
        result['events'].append(event)
        event_delete(event_get(event))
        for ed in event_data_all(event):
            if 'event_data' not in result:
                result['event_data'] = list()
            result['event_data'].append(ed['_id'])
            event_data_delete(ed)
    for ed in event_data_all(brick['_id']):
        if 'event_data' not in result:
            result['event_data'] = list()
        result['event_data'].append(ed['_id'])
        event_data_delete(ed)
    bat_stats_delete(brick['_id'])
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


def __cmd_get_event(data):
    if 'event' not in data:
        return {'s': 22, 'm': 'event is missing in data'}
    return {'event': event_get(data['event'])}


def __cmd_get_event_data(data):
    if 'event_data' not in data:
        return {'s': 24, 'm': 'event_data missing in data'}
    ev = event_get(data['event'])
    return {'event_data': event_data_get(ev, data['event_data'])}


def __cmd_get_event_data_names(data):
    if 'level' not in data:
        return {'s': 30, 'm': 'level is missing in data'}
    valid_levels = ['l', 'b', 'g', 'local', 'brick', 'global']
    if data['level'] not in valid_levels:
        return {'s': 31, 'm': f'invalid level, needs to be one of: {valid_levels}'}
    if 'event' not in data and not data['level'] == 'g' and not data['level'] == 'global':
        return {'s': 22, 'm': 'event is missing in data'}

    if data['level'] == 'g' or data['level'] == 'global':
        event_datas = event_data_all('g')
    elif data['level'] == 'b' or data['level'] == 'brick':
        event = event_get(data['event'])
        event_datas = event_data_all(event['brick_id'])
    else:
        event_datas = event_data_all(data['event'])

    result = list()
    for ed in event_datas:
        result.append(ed['_id'].split('_', 1)[1])
    return {'event_data_names': result}


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
    valid_items = ['bricks', 'temp_sensors', 'latches', 'signals', 'events', 'event_data']
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
    if data['item'] == 'events':
        c = event_count()
    if data['item'] == 'event_data':
        c = event_data_count()
    return {'count': c}


def __cmd_add_event(data):
    if 'brick' not in data:
        return {'s': 11, 'm': 'brick is missing in data'}
    brick = brick_get(data['brick'])
    event = event_get()
    event['brick_id'] = brick['_id']
    brick['events'].append(event['_id'])
    event_save(event)
    brick_save(brick)
    return {'event': event}


def __cmd_delete_event(data):
    if 'brick' not in data:
        return {'s': 11, 'm': 'brick is missing in data'}
    if 'event' not in data:
        return {'s': 22, 'm': 'event is missing in data'}
    result = {'event': data['event'], 'event_data': list()}
    brick = brick_get(data['brick'])
    brick["events"].remove(data['event'])
    event_delete(event_get(data['event']))
    for ed in event_data_all(data['event']):
        event_data_delete(ed)
        result['event_data'].append(ed['_id'])
    brick_save(brick)
    return {'deleted': result}


def __cmd_get_event_commands(data):
    return {'commands': list(event_commands.keys())}


def __cmd_get_event_reactions(data):
    return {'reactions': list(event_reactions.keys())}


def __cmd_add_event_reaction(data):
    if 'event_data' not in data:
        return {'s': 24, 'm': 'event_data is missing in data'}
    if 'event_reaction' not in data:
        return {'s': 25, 'm': 'event_reaction is missing in data'}
    event = event_get(data['event'])
    event['reactions'].append([data['event_reaction'], data['event_data']])
    event_save(event)
    return {'event': event}


def __cmd_delete_event_reaction(data):
    if 'event' not in data:
        return {'s': 22, 'm': 'event is missing in data'}
    if 'pos' not in data:
        return {'s': 26, 'm': 'pos is missing in data'}
    event = event_get(data['event'])
    if data['pos'] not in range(0, len(event['reactions'])):
        return {'s': 7, 'm': f"invalid index range(0, {len(event['reactions']) - 1}) for pos"}
    event['reactions'].pop(data['pos'])
    event_save(event)
    return {'event': event}


def __cmd_replace_event_data(data):
    if 'event_data' not in data:
        return {'s': 24, 'm': 'event_data missing in data'}
    if 'content' not in data:
        return {'s': 27, 'm': 'content missing in data'}
    if not isinstance(data['content'], dict):
        return {'s': 29, 'm': 'content needs to be a dict'}
    event = event_get(data['event'])
    ed = event_data_get(event, data['event_data'])
    data['content']['_id'] = ed['_id']
    event_data_save(data['content'])
    return {'event_data': data['content']}


def __cmd_update_event_data(data):
    if 'event_data' not in data:
        return {'s': 24, 'm': 'event_data missing in data'}
    if 'content' not in data:
        return {'s': 27, 'm': 'content missing in data'}
    if not isinstance(data['content'], dict):
        return {'s': 29, 'm': 'content needs to be a dict'}
    event = event_get(data['event'])
    ed = event_data_get(event, data['event_data'])
    ed_id = ed['_id']
    ed.update(data['content'])
    ed['_id'] = ed_id
    event_data_save(ed)
    return {'event_data': ed}


def __cmd_delete_event_data(data):
    if 'event_data' not in data:
        return {'s': 24, 'm': 'event_data missing in data'}
    event = event_get(data['event'])
    ed = event_data_get(event, data['event_data'])
    result = {'event_data': ed['_id']}
    event_data_delete(ed)
    return {'deleted': result}


admin_commands = {
    'get_bricks': __cmd_get_bricks,
    'get_brick': __cmd_get_brick,
    'set': __cmd_set,
    'delete_brick': __cmd_delete_brick,
    'get_temp_sensor': __cmd_get_temp_sensor,
    'get_latch': __cmd_get_latch,
    'get_signal': __cmd_get_signal,
    'get_event': __cmd_get_event,
    'get_event_data': __cmd_get_event_data,
    'get_event_data_names': __cmd_get_event_data_names,
    'get_features': __cmd_get_features,
    'get_version': __cmd_get_version,
    'get_count': __cmd_get_count,
    'add_event': __cmd_add_event,
    'delete_event': __cmd_delete_event,
    'get_event_commands': __cmd_get_event_commands,
    'get_event_reactions': __cmd_get_event_reactions,
    'add_event_reaction': __cmd_add_event_reaction,
    'delete_event_reaction': __cmd_delete_event_reaction,
    'replace_event_data': __cmd_replace_event_data,
    'update_event_data': __cmd_update_event_data,
    'delete_event_data': __cmd_delete_event_data,
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
    if 'event' in data:
        if not event_exists(data['event']):
            return {'s': 21, 'm': 'invalid event'}
    if 'event_data' in data:
        if 'event' not in data:
            return {'s': 22, 'm': 'event is missing in data'}
    if 'event_reaction' in data:
        if 'event' not in data:
            return {'s': 22, 'm': 'event is missing in data'}
        if data['event_reaction'] not in event_reactions:
            return {'s': 23, 'm': 'invalid event_reaction'}

    result.update(admin_commands[data['command']](data))
    return result
