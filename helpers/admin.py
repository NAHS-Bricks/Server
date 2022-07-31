from connector.mongodb import mongodb_lock_acquire, mongodb_lock_release
from connector.mongodb import brick_exists, brick_get, brick_save, brick_delete, brick_all, brick_all_ids, brick_count
from connector.mongodb import temp_sensor_exists, temp_sensor_delete, temp_sensor_get, temp_sensor_save, temp_sensor_count
from connector.mongodb import humid_exists, humid_delete, humid_get, humid_save, humid_count
from connector.mongodb import latch_exists, latch_get, latch_save, latch_delete, latch_count
from connector.mongodb import signal_exists, signal_all, signal_delete, signal_count, signal_get, signal_save
from connector.mongodb import fwmetadata_get, fwmetadata_all, fwmetadata_count, fwmetadata_search, fwmetadata_latest, fwmetadata_delete
from connector.mongodb import fanctl_all, fanctl_delete, fanctl_exists, fanctl_get, fanctl_save, fanctl_count
from connector.influxdb import temp_delete, bat_stats_delete, latch_delete as latch_metrics_delete, humid_delete as humid_metrics_delete
from connector.influxdb import signal_delete as signal_metrics_delete, fanctl_delete as fanctl_metrics_delete
from connector.ds import dsfirmware_get, dsfirmware_get_latest, dsfirmware_get_used, dsfirmware_get_bin
from connector.mqtt import signal_send
from connector.brick import activate as brick_activator
from connector.s3 import firmware_exists, firmware_delete, firmware_filename
from helpers.feature_versioning import features_available
from helpers.current_version import current_brickserver_version
import time
import cherrypy


def __set_desc(data):
    if 'brick' in data:
        brick = brick_get(data['brick'])
        brick['desc'] = data['value']
        brick_save(brick)
    elif 'temp_sensor' in data:
        sensor = temp_sensor_get(data['temp_sensor'])
        sensor['desc'] = data['value']
        temp_sensor_save(sensor)
    elif 'humid_sensor' in data:
        sensor = humid_get(data['humid_sensor'])
        sensor['desc'] = data['value']
        humid_save(sensor)
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
    elif 'fanctl' in data:
        fanctl = fanctl_get(*data['fanctl'].split('_'))
        fanctl['desc'] = data['value']
        fanctl_save(fanctl)
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
    valid_values = ['metric', 'ui', 'mqtt']
    if data['value'] not in valid_values:
        return {'s': 7, 'm': 'invalid value needs to be one of: ' + str(valid_values)}
    if 'temp_sensor' in data:
        sensor = temp_sensor_get(data['temp_sensor'])
        if data['value'] not in sensor['disables']:
            sensor['disables'].append(data['value'])
            temp_sensor_save(sensor)
    elif 'humid_sensor' in data:
        sensor = humid_get(data['humid_sensor'])
        if data['value'] not in sensor['disables']:
            sensor['disables'].append(data['value'])
            humid_save(sensor)
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
    elif 'fanctl' in data:
        fanctl = fanctl_get(*data['fanctl'].split('_'))
        if data['value'] not in fanctl['disables']:
            fanctl['disables'].append(data['value'])
            fanctl_save(fanctl)
    else:
        return {'s': 14, 'm': 'no object given for adding disable'}
    return {}


def __set_del_disable(data):
    valid_values = ['metric', 'ui', 'mqtt']
    if data['value'] not in valid_values:
        return {'s': 7, 'm': 'invalid value needs to be one of: ' + str(valid_values)}
    if 'temp_sensor' in data:
        sensor = temp_sensor_get(data['temp_sensor'])
        if data['value'] in sensor['disables']:
            sensor['disables'].remove(data['value'])
            temp_sensor_save(sensor)
    elif 'humid_sensor' in data:
        sensor = humid_get(data['humid_sensor'])
        if data['value'] in sensor['disables']:
            sensor['disables'].remove(data['value'])
            humid_save(sensor)
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
    elif 'fanctl' in data:
        fanctl = fanctl_get(*data['fanctl'].split('_'))
        if data['value'] in fanctl['disables']:
            fanctl['disables'].remove(data['value'])
            fanctl_save(fanctl)
    else:
        return {'s': 14, 'm': 'no object given for deleteing disable'}
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


def __set_sleep_disabled(data):
    if 'brick' not in data:
        return {'s': 11, 'm': 'brick is missing in data'}
    if not isinstance(data['value'], bool):
        return {'s': 7, 'm': 'invalid value, needs to be a bool'}
    brick = brick_get(data['brick'])
    if 'sleep' not in brick['features']:
        return {'s': 34, 'm': 'sleep not in brick-features'}
    if not brick['features']['sleep'] >= 1.01:
        return {'s': 35, 'm': 'feature version not satisfied (sleep >= 1.01)'}
    brick['sleep_set_disabled'] = data['value']
    brick_save(brick)
    return {}


def __set_otaupdate(data):
    if 'brick' not in data:
        return {'s': 11, 'm': 'brick is missing in data'}
    if data['value'] not in ['requested', 'canceled']:
        return {'s': 7, 'm': 'invalid value, needs to be a "requested" or "canceled"'}
    brick = brick_get(data['brick'])
    if not brick['features']['os'] >= 1.01:
        return {'s': 35, 'm': 'feature version not satisfied (os >= 1.01)'}
    brick['otaUpdate'] = data['value']
    brick_save(brick)
    return {}


def __set_fanctl_mode(data):
    if 'fanctl' not in data:
        return {'s': 41, 'm': 'fanctl is missing in data'}
    valid_values = [0, 1, 2]
    if data['value'] not in valid_values:
        return {'s': 7, 'm': f'invalid value, needs to be one of {valid_values}'}
    fanctl = fanctl_get(*data['fanctl'].split('_'))
    fanctl['mode'] = data['value']
    fanctl['mode_transmitted_ts'] = None
    fanctl_save(fanctl)
    return {}


def __set_fanctl_duty(data):
    if 'fanctl' not in data:
        return {'s': 41, 'm': 'fanctl is missing in data'}
    if data['value'] not in range(0, 101):
        return {'s': 7, 'm': 'invalid value, needs to be in range of 0 to 100'}
    fanctl = fanctl_get(*data['fanctl'].split('_'))
    fanctl['dutyCycle'] = data['value']
    fanctl['dutyCycle_transmitted_ts'] = None
    fanctl_save(fanctl)
    return {}


def __set_fanctl_state(data):
    if 'fanctl' not in data:
        return {'s': 41, 'm': 'fanctl is missing in data'}
    if data['value'] not in range(0, 2):
        return {'s': 7, 'm': 'invalid value, needs to be 0 or 1'}
    fanctl = fanctl_get(*data['fanctl'].split('_'))
    fanctl['state_should'] = data['value']
    fanctl_save(fanctl)
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


def __set_bat_adc5v(data):
    if 'brick' not in data:
        return {'s': 11, 'm': 'brick is missing in data'}
    brick = brick_get(data['brick'])
    if 'bat' not in brick['features']:
        return {'s': 36, 'm': 'bat not in brick-features'}
    if data['value'] not in range(0, 1024):
        return {'s': 7, 'm': 'invalid value range(0, 1023)'}
    brick['bat_adc5V'] = data['value']
    brick['bat_init_ts'] = None
    brick['bat_init_voltage'] = None
    brick['admin_override'][data['key']] = data['value']
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
    if 'mqtt' not in signal['disables']:
        signal_send(signal['_id'], signal['state'], False)
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
    'bat_solar_charging': __set_bat_solar_charging,
    'sleep_disabled': __set_sleep_disabled,
    'otaupdate': __set_otaupdate,
    'fanctl_mode': __set_fanctl_mode,
    'fanctl_duty': __set_fanctl_duty,
    'fanctl_state': __set_fanctl_state
}


_set_indirect = {
    'temp_precision': __set_temp_precision,
    'bat_adc5V': __set_bat_adc5v,
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
    if 'humid' in brick['features']:
        result['humid_sensors'] = list()
        for sensor in brick['humid_sensors']:
            result['humid_sensors'].append(sensor)
            humid_delete(sensor)
            humid_metrics_delete(sensor)
    if 'latch' in brick['features']:
        result['latches'] = list()
        for i in range(0, brick['latch_count']):
            result['latches'].append(brick['_id'] + '_' + str(i))
            latch_delete(brick['_id'], i)
            latch_metrics_delete(brick['_id'], i)
    if 'signal' in brick['features']:
        result['signals'] = list()
        for signal in signal_all(brick_id=brick['_id']):
            result['signals'].append(signal['_id'])
            signal_delete(signal)
            signal_metrics_delete(*signal['_id'].split('_'))
    if 'fanctl' in brick['features']:
        result['fanctl'] = list()
        for fanctl in fanctl_all(brick['_id']):
            result['fanctl'].append(fanctl['_id'])
            fanctl_delete(fanctl)
            fanctl_metrics_delete(fanctl['_id'])
    bat_stats_delete(brick['_id'])
    brick_delete(brick['_id'])
    return {'deleted': result}


def __cmd_get_temp_sensor(data):
    if 'temp_sensor' not in data:
        return {'s': 12, 'm': 'temp_sensor is missing in data'}
    return {'temp_sensor': temp_sensor_get(data['temp_sensor'])}


def __cmd_get_humid_sensor(data):
    if 'humid_sensor' not in data:
        return {'s': 33, 'm': 'humid_sensor is missing in data'}
    return {'humid_sensor': humid_get(data['humid_sensor'])}


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


def __cmd_get_fanctl(data):
    if 'fanctl' not in data:
        return {'s': 41, 'm': 'fanctl is missing in data'}
    return {'fanctl': fanctl_get(*data['fanctl'].split('_'))}


def __cmd_get_firmware(data):
    if 'brick_type' in data and 'version' in data and data['brick_type'] is not None and data['version'] is not None:
        fw = fwmetadata_get(brick_type=data['brick_type'], version=data['version'])
    elif 'brick_type' in data and 'sketchmd5' in data and data['brick_type'] is not None and data['sketchmd5'] is not None:
        fw = fwmetadata_search(brick_type=data['brick_type'], sketchMD5=data['sketchmd5'])
    elif 'latest' in data and data['latest'] is not None:
        fw = fwmetadata_latest(brick_type=data['latest'])
    else:
        return {'s': 37, 'm': 'specifiers are missing possible is: (brick_type and version) or (brick_type and sketchmd5) or latest'}
    if fw is not None:
        fw['bin'] = firmware_exists(fwmetadata=fw)
    return {'firmware': fw}


def __cmd_get_firmwares(data):
    if 'brick_type' in data and data['brick_type'] is not None and not data['brick_type'] == '':
        fws = fwmetadata_all(brick_type=data['brick_type'])
    else:
        fws = fwmetadata_all()
    result = list()
    for fw in fws:
        fw['bin'] = firmware_exists(fwmetadata=fw)
        result.append(fw)
    return {'firmwares': result}


def __cmd_fetch_firmware(data):
    what = ['latest', 'used', 'specific', 'bin']
    if data.get('what') not in what:
        return {'s': 7, 'm': f"invalid value: what is '{data.get('what')}' but needs to be one of: {what}"}
    result = dict()
    if data.get('what') == 'specific':
        if data.get('brick_type') is None:
            return {'s': 38, 'm': 'brick_type is missing in data'}
        if data.get('version') is None:
            return {'s': 39, 'm': 'version is missing in data'}
        fw_name = dsfirmware_get(brick_type=data.get('brick_type'), version=data.get('version'))
        if fw_name is not None:
            result = {'metadata': [fw_name]}
        else:
            result = {'metadata': []}
    elif data.get('what') == 'bin':
        if data.get('brick_type') is None:
            return {'s': 38, 'm': 'brick_type is missing in data'}
        fw_name = dsfirmware_get_bin(brick_type=data.get('brick_type'), version=data.get('version'))
        if fw_name is not None:
            result = {'firmware': [fw_name + '.bin']}
        else:
            result = {'firmware': []}
    elif data.get('what') == 'latest':
        result = {'metadata': dsfirmware_get_latest(brick_type=data.get('brick_type'))}
    elif data.get('what') == 'used':
        result = {'metadata': dsfirmware_get_used(brick_id=data.get('brick'))}
    return {'fetched': result}


def __cmd_delete_firmware(data):
    if 'brick_type' in data and 'version' in data and data['brick_type'] is not None and data['version'] is not None:
        fw = fwmetadata_get(brick_type=data['brick_type'], version=data['version'])
    elif 'brick_type' in data and 'sketchmd5' in data and data['brick_type'] is not None and data['sketchmd5'] is not None:
        fw = fwmetadata_search(brick_type=data['brick_type'], sketchMD5=data['sketchmd5'])
    elif 'latest' in data and data['latest'] is not None:
        fw = fwmetadata_latest(brick_type=data['latest'])
    else:
        return {'s': 37, 'm': 'specifiers are missing possible is: (brick_type and version) or (brick_type and sketchmd5) or latest'}
    result = dict()
    if firmware_exists(fwmetadata=fw):
        firmware_delete(fwmetadata=fw)
        result['firmware'] = firmware_filename(fwmetadata=fw)
    if not data.get('bin_only', False):
        fwmetadata_delete(metadata=fw)
        result['metadata'] = fw.get('_id')
    return {'deleted': result}


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
    valid_items = ['bricks', 'temp_sensors', 'humid_sensors', 'latches', 'signals', 'firmwares', 'fanctl']
    if data['item'] not in valid_items:
        return {'s': 17, 'm': 'invalid item given. Needs to be one of: ' + str(valid_items)}
    c = 0
    if data['item'] == 'bricks':
        c = brick_count()
    elif data['item'] == 'temp_sensors':
        c = temp_sensor_count()
    elif data['item'] == 'humid_sensors':
        c = humid_count()
    elif data['item'] == 'latches':
        c = latch_count()
    elif data['item'] == 'signals':
        c = signal_count()
    elif data['item'] == 'firmwares':
        c = fwmetadata_count()
    elif data['item'] == 'fanctl':
        c = fanctl_count()
    return {'count': c}


admin_commands = {
    'get_bricks': __cmd_get_bricks,
    'get_brick': __cmd_get_brick,
    'set': __cmd_set,
    'delete_brick': __cmd_delete_brick,
    'get_temp_sensor': __cmd_get_temp_sensor,
    'get_humid_sensor': __cmd_get_humid_sensor,
    'get_latch': __cmd_get_latch,
    'get_signal': __cmd_get_signal,
    'get_fanctl': __cmd_get_fanctl,
    'get_firmware': __cmd_get_firmware,
    'get_firmwares': __cmd_get_firmwares,
    'fetch_firmware': __cmd_fetch_firmware,
    'delete_firmware': __cmd_delete_firmware,
    'get_features': __cmd_get_features,
    'get_version': __cmd_get_version,
    'get_count': __cmd_get_count
}


def __thread_save_execution(data):
    if data['command'].startswith('get_') or data['command'].startswith('fetch_') or data['command'] == 'delete_firmware':
        return admin_commands[data['command']](data)

    brick_id = None
    if 'brick' in data:
        brick_id = data['brick']
    elif 'latch' in data:
        brick_id = data['latch'].split('_', 1)[0]
    elif 'signal' in data:
        brick_id = data['signal'].split('_', 1)[0]
    elif 'fanctl' in data:
        brick_id = data['fanctl'].split('_', 1)[0]
    elif 'temp_sensor' in data:
        for brick in brick_all():
            if 'temp' in brick['features'] and data['temp_sensor'] in brick['temp_sensors']:
                brick_id = brick['_id']
                break
    elif 'humid_sensor' in data:
        for brick in brick_all():
            if 'humid' in brick['features'] and data['humid_sensor'] in brick['humid_sensors']:
                brick_id = brick['_id']
                break

    if brick_id is None and 'environment' in cherrypy.config and cherrypy.config['environment'] == 'test_suite' and not cherrypy.config['ignore_brick_identification']:  # pragma: no cover
        raise Exception(f"brick can't be identified by: {data}")

    mongodb_lock_acquire(brick_id)
    result = admin_commands[data['command']](data)
    if 'activate' in data and data['activate']:
        brick_activator(brick_id=brick_id)
    mongodb_lock_release(brick_id)
    return result


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
    if 'humid_sensor' in data and not humid_exists(data['humid_sensor']):
        return {'s': 32, 'm': 'invalid humid_sensor'}
    if 'latch' in data:
        brick_id, latch_id = data['latch'].split('_')
        if not latch_exists(brick_id, latch_id):
            return {'s': 9, 'm': 'invalid latch'}
    if 'signal' in data:
        brick_id, signal_id = data['signal'].split('_')
        if not signal_exists(brick_id, signal_id):
            return {'s': 20, 'm': 'invalid signal'}
    if 'fanctl' in data and not fanctl_exists(*data['fanctl'].split('_')):
        return {'s': 40, 'm': 'invalid fanctl'}

    result.update(__thread_save_execution(data))
    return result
