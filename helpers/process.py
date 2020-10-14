from helpers.config import *
from datetime import datetime, timedelta

def __process_t(brick_new, brick_old):
    if 'temp' in brick_new['features'] and 'temp' in brick_old['features']:
        max_diff = 0
        for sensor in [sensor for sensor in brick_new['last_temps'] if sensor in brick_old['last_temps']]:
            diff = abs(brick_old['last_temps'][sensor] - brick_new['last_temps'][sensor])
            max_diff = diff if diff > max_diff else max_diff
        brick_new['max_temp_diff'] = max_diff


def __process_b(brick_new, brick_old):
    if 'bat' in brick_new['features']:
        if brick_new['last_bat_reading'] < 3.5:
            send_telegram('Charge bat on ' + brick_new['id'] + ' (' + brick_new['desc'] + ') it reads ' + str(brick_new['last_bat_reading']) + ' Volts')


def __process_y(brick_new, brick_old):
    result = []
    if brick_new['initalized']:
        result.append('request_version')
        result.append('request_features')
    if 'bat' in brick_new['features'] and 'bat' in brick_old['features']:
        if not brick_new['bat_charging'] and brick_old['bat_charging']:
            result.append('request_bat_voltage')
        if not brick_new['bat_charging'] and not brick_new['bat_charging_standby'] and (brick_old['bat_charging'] or brick_old['bat_charging_standby']):
            result.append('request_bat_voltage')
    return result


process = {
    't': __process_t,
    'b': __process_b,
    'y': __process_y
}
