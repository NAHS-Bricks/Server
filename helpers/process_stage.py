from helpers.shared import send_telegram
from helpers.mongodb import temp_sensor_get, latch_get
from helpers.influxdb import temp_store, bat_level_store, latch_store
from datetime import datetime, timedelta
import os


def __process_t(brick_new, brick_old):
    if 'temp' not in brick_new['features']:  # pragma: no cover
        return
    for sensor in [sensor for sensor in [temp_sensor_get(sensor) for sensor in brick_new['temp_sensors']] if sensor['last_reading'] is not None]:
        temp_store(sensor['last_reading'], sensor['_id'], brick_new['last_ts'], sensor['desc'], brick_new['_id'], brick_new['desc'])
    if 'temp' in brick_old['features']:
        max_diff = 0
        for sensor in [sensor for sensor in [temp_sensor_get(s) for s in brick_new['temp_sensors']] if sensor['last_reading'] and sensor['prev_reading']]:
            diff = abs(sensor['prev_reading'] - sensor['last_reading'])
            max_diff = diff if diff > max_diff else max_diff
        brick_new['temp_max_diff'] = max_diff


def __process_b(brick_new, brick_old):
    if 'bat' in brick_new['features']:
        # Store Data to InfluxDB
        bat_level_store(brick_new['bat_last_reading'], brick_new['bat_charging'], brick_new['bat_charging_standby'], brick_new['_id'], brick_new['last_ts'], brick_new['desc'])
        # Check for low-bat warning
        if brick_new['bat_last_reading'] < 3.4:
            send_telegram('Charge bat on ' + (brick_new['_id'] if brick_new['desc'] is None or brick_new['desc'] == '' else brick_new['desc']) + ' it reads ' + str(round(brick_new['bat_last_reading'], 3)) + ' Volts')
    if 'bat' in brick_new['features'] and 'bat' in brick_old['features']:
        if brick_new['bat_charging'] and brick_new['bat_last_reading'] >= 4.15 and brick_old['bat_last_reading'] < 4.15:
            send_telegram('Bat charged over 4.15Volts on ' + (brick_new['_id'] if brick_new['desc'] is None or brick_new['desc'] == '' else brick_new['desc']))


def __process_l(brick_new, brick_old):
    if 'latch' not in brick_new['features']:  # pragma: no cover
        return
    brick_new['latch_triggerstate_received'] = False
    for latch in [latch for latch in [latch_get(brick_new['_id'], lid) for lid in range(0, brick_new['latch_count'])] if latch['last_state'] is not None]:
        latch_store(latch['last_state'], latch['_id'], brick_new['last_ts'], latch['desc'], brick_new['desc'])
        if latch['last_state'] > 1:
            brick_new['latch_triggerstate_received'] = True


def __process_y(brick_new, brick_old):
    result = []
    if brick_new['initalized']:
        result.append('request_versions')
        result.append('request_type')
        if 'temp' in brick_new['features']:
            result.append('request_temp_corr')
            result.append('request_temp_precision')
        if 'latch' in brick_new['features']:
            result.append('update_latch_triggers')
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
            send_telegram('Charging finished on ' + (brick_new['_id'] if brick_new['desc'] is None or brick_new['desc'] == '' else brick_new['desc']))
        if not brick_new['bat_charging'] and not brick_new['bat_charging_standby'] and (brick_old['bat_charging'] or brick_old['bat_charging_standby']):
            brick_new['bat_periodic_voltage_request'] = 10
            result.append('request_bat_voltage')
    return result


process = {
    't': __process_t,
    'b': __process_b,
    'l': __process_l,
    'y': __process_y
}
