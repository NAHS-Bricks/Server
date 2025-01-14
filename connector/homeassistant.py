from connector.mongodb import brick_get
from connector.mqtt import _publish_async
from helpers.current_version import current_brickserver_version as bs_version
from helpers.shared import config


discovery_prefix = config['mqtt']['ha_discovery_prefix']

# brick_type to model (mdl) map
type_mdl_map = {
    1: 'TempBrick'
}

# brick_type to hw_version (hw) map
type_hw_map = {
    1: '1.0'
}


def __cmp_bat_percent(brick_id):
    result = {
        'platform': 'sensor',
        'unique_id': f'brick{brick_id}batvoltage',
        'name': 'Battery',
        'device_class': 'battery',
        'state_topic': '~/bat/voltage',
        'value_template': '{{ 100 / 0.8 * (min([value, 4.2]) - 3.4) | round(0) }}'
    }
    return result


def __cmp_bat_prediction(brick_id):
    result = {
        'platform': 'sensor',
        'unique_id': f'brick{brick_id}batprediction',
        'name': 'Battery Prediction',
        'device_class': 'duration',
        'state_topic': '~/bat/prediction',
        'unit_of_measurement': 'd',
        'suggested_display_precision': 0,
        'icon': 'mdi:battery-clock-outline'
    }
    return result


def __cmp_temp(brick_id, sensor):
    pass


def __cmp_humid(brick_id, sensor):
    pass


def __cmp_latch(brick_id, sensor):
    pass


def send_config(brick=None, brick_id=None):
    if not brick:
        brick = brick_get(brick_id)
    if not brick['ha_enabled']:
        return
    brick_id = brick['id']
    payload = dict()
    payload['~'] = f'/brick/{brick["id"]}'
    payload['device'] = {'ids': brick_id, 'name': brick['desc'], 'mf': 'NiJOs', 'mdl': type_mdl_map[brick['type']], 'hw': type_hw_map[brick['type']]}
    payload['origin'] = {'name': 'BrickServer', 'sw': bs_version, 'url': 'https://bricks.nijos.de'}
    payload['components'] = dict()
    for feature in brick['features'].keys():
        if feature == 'bat':
            payload['components']['battery'] = __cmp_bat_percent(brick_id)
            payload['components']['battery_prediction'] = __cmp_bat_prediction(brick_id)
        elif feature == 'temp':
            pass
        elif feature == 'humid':
            pass
        elif feature == 'latch':
            pass
    _publish_async(topic=f'{discovery_prefix}/device/{brick_id}/config', payload=payload)
