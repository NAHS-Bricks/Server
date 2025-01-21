from connector.mongodb import brick_get, brick_all, temp_sensor_get, humid_get, latch_get
from connector.mqtt import _publish_async, bat_level_send, temp_send, humid_send, latch_send
from helpers.current_version import current_brickserver_version as bs_version
from helpers.shared import config
from multiprocessing import Process
import json


async_listener = None
discovery_prefix = config['mqtt']['ha_discovery_prefix']

# brick_type to model (mdl) map
type_mdl_map = {
    1: 'TempBrick',
    2: 'LatchBrick',
    3: 'SignalBrick',
    4: 'RackBrick',
    5: 'RHTBrick',
    6: 'HeatBrick'
}

# brick_type to hw_version (hw) map
type_hw_map = {
    1: '1.0',
    2: '1.0',
    3: '1.0',
    4: '1.0',
    5: '1.0',
    6: '1.0'
}


def __cmp_bat_percent(brick_id):
    result = {
        'platform': 'sensor',
        'unique_id': f'brick{brick_id}batvoltage',
        'name': 'Battery',
        'device_class': 'battery',
        'state_topic': f'brick/{brick_id}/bat/voltage',
        'value_template': '{{ 100 / 0.8 * (min([value, 4.2]) - 3.4) | round(0) }}'
    }
    return result


def __cmp_bat_prediction(brick_id):
    result = {
        'platform': 'sensor',
        'unique_id': f'brick{brick_id}batprediction',
        'name': 'Battery Prediction',
        'device_class': 'duration',
        'state_topic': f'brick/{brick_id}/bat/prediction',
        'unit_of_measurement': 'd',
        'suggested_display_precision': 0,
        'icon': 'mdi:battery-clock-outline'
    }
    return result


def __cmp_temp(brick_id, sensor):
    sensor_id = sensor['_id']
    result = {
        'platform': 'sensor',
        'unique_id': f'brick{brick_id}temp{sensor_id}',
        'device_class': 'temperature',
        'state_topic': f'brick/{brick_id}/temp/{sensor_id}',
        'name': f'Temperature {sensor_id}'
    }
    if sensor['desc'] is not None and not sensor['desc'] == '':
        result['name'] = sensor['desc']
    return result


def __cmp_humid(brick_id, sensor):
    sensor_id = sensor['_id']
    result = {
        'platform': 'sensor',
        'unique_id': f'brick{brick_id}humid{sensor_id}',
        'device_class': 'humidity',
        'state_topic': f'brick/{brick_id}/humid/{sensor_id}',
        'name': f'Humidity {sensor_id}'
    }
    if sensor['desc'] is not None and not sensor['desc'] == '':
        result['name'] = sensor['desc']
    return result


def __cmp_latch(brick_id, sensor):
    sensor_id = sensor['_id']
    _, latch_id = sensor_id.split('_')
    result = {
        'platform': 'sensor',
        'unique_id': f'brick{brick_id}latch{sensor_id}',
        'device_class': 'enum',
        'options': sensor['states_desc'],
        'state_topic': f'brick/{brick_id}/latch/{sensor_id}',
        'name': f'Latch {latch_id}'
    }
    if sensor['desc'] is not None and not sensor['desc'] == '':
        result['name'] = sensor['desc']
    return result


def send_device_config(brick=None, brick_id=None):
    if not config['allow']['homeassistant']:
        return
    if not brick:
        brick = brick_get(brick_id)
    if not brick['ha_enabled']:
        return
    brick_id = brick['_id']
    payload = dict()
    payload['device'] = {'ids': brick_id, 'name': brick_id, 'mf': 'NiJOs', 'mdl': type_mdl_map[brick['type']], 'hw': type_hw_map[brick['type']]}
    if brick['desc'] is not None and not brick['desc'] == '':
        payload['device']['name'] = brick['desc']
    payload['origin'] = {'name': 'BrickServer', 'sw': bs_version, 'url': 'https://bricks.nijos.de'}
    payload['components'] = dict()
    for feature in brick['features'].keys():
        if feature == 'bat':
            payload['components']['battery'] = __cmp_bat_percent(brick_id)
            payload['components']['battery_prediction'] = __cmp_bat_prediction(brick_id)
        elif feature == 'temp':
            for sensor_id in brick['temp_sensors']:
                sensor = temp_sensor_get(sensor_id)
                if 'mqtt' not in sensor['disables']:
                    payload['components'][f'temp{sensor_id}'] = __cmp_temp(brick_id, sensor)
        elif feature == 'humid':
            for sensor_id in brick['humid_sensors']:
                sensor = humid_get(sensor_id)
                if 'mqtt' not in sensor['disables']:
                    payload['components'][f'humid{sensor_id}'] = __cmp_humid(brick_id, sensor)
        elif feature == 'latch':
            for latch_id in range(brick['latch_count']):
                latch = latch_get(brick_id, latch_id)
                if 'mqtt' not in latch['disables']:
                    payload['components'][f'latch{latch_id}'] = __cmp_latch(brick_id, latch)
    _publish_async(topic=f'{discovery_prefix}/device/{brick_id}/config', payload=json.dumps(payload))


def send_sensor_states(brick=None, brick_id=None):
    if not config['allow']['homeassistant']:
        return
    if not brick:
        brick = brick_get(brick_id)
    if not brick['ha_enabled']:
        return
    brick_id = brick['_id']

    if 'bat' in brick['features']:
        if brick['bat_last_reading'] > 0:
            bat_level_send(brick_id, brick['bat_last_reading'], brick['bat_runtime_prediction'])

    if 'temp' in brick['features']:
        for sensor in [temp_sensor_get(sid) for sid in brick['temp_sensors']]:
            if 'mqtt' in sensor['disables'] or sensor['last_reading'] is None:
                continue
            temp_send(sensor['_id'], sensor['last_reading'], brick_id)

    if 'humid' in brick['features']:
        for sensor in [humid_get(sid) for sid in brick['humid_sensors']]:
            if 'mqtt' in sensor['disables'] or sensor['last_reading'] is None:
                continue
            humid_send(sensor['_id'], sensor['last_reading'], brick_id)

    if 'latch' in brick['features']:
        for latch in [latch_get(brick_id, lid) for lid in range(brick['latch_count'])]:
            if 'mqtt' in latch['disables'] or latch['last_state'] is None:
                continue
            latch_send(latch['_id'], latch['last_state'])


def send_all_configs():
    if not config['allow']['homeassistant']:
        return
    for brick in brick_all():
        send_device_config(brick=brick)
    for brick in brick_all():
        send_sensor_states(brick=brick)


def start_async_listener():  # pragma: no cover
    def _async_listener():
        from paho.mqtt import subscribe

        def _on_message(client, userdata, message):
            if message.payload.decode('utf-8') == config['mqtt']['ha_birth_msg']:
                print('Received birth message from Home Assistant. Transmitting Brick-Configs ans latest Seansor-States')
                send_all_configs()

        subscribe.callback(_on_message,
                           f'{discovery_prefix}/status',
                           hostname=config['mqtt']['server'],
                           port=config['mqtt']['port'],
                           transport='tcp')

    global async_listener
    if async_listener is None and config['allow']['homeassistant']:
        async_listener = Process(target=_async_listener, args=(), daemon=True)
        async_listener.start()
