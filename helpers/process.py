from helpers.config import *
from datetime import datetime, timedelta


def __process_t(brick_new, brick_old):
    global temp_sensors
    if 'temp' in brick_new['features'] and 'temp' in brick_old['features']:
        max_diff = 0
        for sensor in [sensor for sensor in brick_new['temp_sensors'] if temp_sensors[sensor]['last_reading'] and temp_sensors[sensor]['prev_reading']]:
            diff = abs(temp_sensors[sensor]['prev_reading'] - temp_sensors[sensor]['last_reading'])
            max_diff = diff if diff > max_diff else max_diff
        brick_new['temp_max_diff'] = max_diff


def __process_b(brick_new, brick_old):
    if 'bat' in brick_new['features']:
        if brick_new['bat_last_reading'] < 3.5:
            send_telegram('Charge bat on ' + brick_new['id'] + ' (' + brick_new['desc'] + ') it reads ' + str(brick_new['bat_last_reading']) + ' Volts')
    if 'bat' in brick_new['features'] and 'bat' in brick_old['features']:
        if brick_new['bat_charging'] and brick_new['bat_last_reading'] >= 4.15 and brick_old['bat_last_reading'] < 4.15:
            send_telegram('Bat charged over 4.15Volts on ' + brick_new['id'] + ' (' + brick_new['desc'] + ')')


def __process_y(brick_new, brick_old):
    result = []
    if brick_new['initalized']:
        result.append('request_version')
        result.append('request_features')
    if 'bat' in brick_new['features']:
        if brick_new['bat_charging']:
            brick_new['bat_periodic_voltage_request'] -= 1
            if brick_new['bat_periodic_voltage_request'] <= 0:
                brick_new['bat_periodic_voltage_request'] = 10
                result.append('request_bat_voltage')
    if 'bat' in brick_new['features'] and 'bat' in brick_old['features']:
        if not brick_new['bat_charging'] and brick_old['bat_charging']:
            brick_new['bat_periodic_voltage_request'] = 10
            result.append('request_bat_voltage')
        if not brick_new['bat_charging'] and brick_old['bat_charging'] and brick_new['bat_charging_standby']:
            send_telegram('Charging finished on ' + brick_new['id'] + ' (' + brick_new['desc'] + ')')
        if not brick_new['bat_charging'] and not brick_new['bat_charging_standby'] and (brick_old['bat_charging'] or brick_old['bat_charging_standby']):
            brick_new['bat_periodic_voltage_request'] = 10
            result.append('request_bat_voltage')
    return result


process = {
    't': __process_t,
    'b': __process_b,
    'y': __process_y
}
