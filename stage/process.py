from helpers.shared import send_telegram, calculate_bat_prediction
from connector.mongodb import temp_sensor_get, humid_get, latch_get
from connector.influxdb import temp_store, humid_store, bat_level_store, bat_charging_store, latch_store
from connector.mqtt import temp_send, humid_send, bat_level_send, bat_charging_send, latch_send
from datetime import datetime, timedelta
import os


def __process_t(brick_new, brick_old):
    if 'temp' not in brick_new['features']:  # pragma: no cover
        return
    for sensor in [sensor for sensor in [temp_sensor_get(sensor) for sensor in brick_new['temp_sensors']] if sensor['last_reading'] is not None]:
        if 'metric' not in sensor['disables']:
            temp_store(sensor['last_reading'], sensor['_id'], brick_new['last_ts'], sensor['desc'], brick_new['_id'], brick_new['desc'])
        if 'mqtt' not in sensor['disables']:
            temp_send(sensor['_id'], sensor['last_reading'], brick_new['_id'])
    if 'temp' in brick_old['features']:
        max_diff = 0
        for sensor in [sensor for sensor in [temp_sensor_get(s) for s in brick_new['temp_sensors']] if sensor['last_reading'] and sensor['prev_reading']]:
            diff = abs(sensor['prev_reading'] - sensor['last_reading'])
            max_diff = diff if diff > max_diff else max_diff
        brick_new['temp_max_diff'] = max_diff


def __process_h(brick_new, brick_old):
    if 'humid' not in brick_new['features']:  # pragma: no cover
        return
    for sensor in [sensor for sensor in [humid_get(sensor) for sensor in brick_new['humid_sensors']] if sensor['last_reading'] is not None]:
        if 'metric' not in sensor['disables']:
            humid_store(sensor['last_reading'], sensor['_id'], sensor['last_ts'], sensor['desc'], brick_new['_id'], brick_new['desc'])
        if 'mqtt' not in sensor['disables']:
            humid_send(sensor['_id'], sensor['last_reading'], brick_new['_id'])
    if 'humid' in brick_old['features']:
        max_diff = 0
        for sensor in [sensor for sensor in [humid_get(s) for s in brick_new['humid_sensors']] if sensor['last_reading'] and sensor['prev_reading']]:
            max_diff = max(max_diff, abs(sensor['prev_reading'] - sensor['last_reading']))
        brick_new['humid_max_diff'] = max_diff


def __process_b(brick_new, brick_old):
    if 'bat' not in brick_new['features']:  # pragma: no cover
        return
    # Check for low-bat warning
    if brick_new['bat_last_reading'] < 3.4:
        send_telegram('Charge bat on ' + (brick_new['_id'] if brick_new['desc'] is None or brick_new['desc'] == '' else brick_new['desc']) + ' it reads ' + str(round(brick_new['bat_last_reading'], 3)) + ' Volts')
    # Calculate bat_runtime_prediction
    brick_new['bat_runtime_prediction'] = (None if (brick_new['bat_charging'] or brick_new['bat_charging_standby']) and not brick_new['bat_solar_charging'] else calculate_bat_prediction(brick_new))
    # Store Data to InfluxDB
    voltage_diff = ((brick_old['bat_last_reading'] - brick_new['bat_last_reading']) if 'bat_last_reading' in brick_old and brick_old['bat_last_reading'] else None)
    bat_level_store(brick_new['bat_last_reading'], voltage_diff, brick_new['bat_runtime_prediction'], brick_new['_id'], brick_new['last_ts'], brick_new['desc'])
    bat_level_send(brick_new['_id'], brick_new['bat_last_reading'], brick_new['bat_runtime_prediction'])
    if 'bat' in brick_old['features']:
        if brick_new['bat_charging'] and brick_new['bat_last_reading'] >= 4.15 and brick_old['bat_last_reading'] < 4.15:
            send_telegram('Bat charged over 4.15Volts on ' + (brick_new['_id'] if brick_new['desc'] is None or brick_new['desc'] == '' else brick_new['desc']))


def __process_l(brick_new, brick_old):
    if 'latch' not in brick_new['features']:  # pragma: no cover
        return
    brick_new['latch_triggerstate_received'] = False
    for latch in [latch for latch in [latch_get(brick_new['_id'], lid) for lid in range(0, brick_new['latch_count'])] if latch['last_state'] is not None]:
        if 'metric' not in latch['disables']:
            latch_store(latch['last_state'], latch['_id'], brick_new['last_ts'], latch['desc'], brick_new['desc'])
        if 'mqtt' not in latch['disables']:
            latch_send(latch['_id'], latch['last_state'])
        if latch['last_state'] > 1:
            brick_new['latch_triggerstate_received'] = True


def __process_y(brick_new, brick_old):
    result = []
    if brick_new['initalized']:
        result.append('request_versions')
        result.append('request_type')
        brick_new['init_ts'] = brick_new['last_ts']
        if 'temp' in brick_new['features']:
            result.append('request_temp_corr')
            result.append('request_temp_precision')
        if 'humid' in brick_new['features']:
            result.append('request_humid_corr')
        if 'latch' in brick_new['features']:
            result.append('update_latch_triggers')
        if 'bat' in brick_new['features']:
            result.append('request_bat_voltage')
            brick_new['bat_init_ts'] = None
            brick_new['bat_init_voltage'] = None
        if 'signal' in brick_new['features']:
            result.append('request_signal_count')
            result.append('update_signal_states')
        if brick_new['features']['all'] >= 1.02:
            result.append('request_delay_default')
    if 'bat' in brick_new['features'] and not brick_new['bat_solar_charging']:
        if brick_new['bat_charging']:
            brick_new['bat_periodic_voltage_request'] -= 1
            if brick_new['bat_periodic_voltage_request'] <= 0:
                brick_new['bat_periodic_voltage_request'] = 10
                result.append('request_bat_voltage')
    if 'bat' in brick_new['features'] and 'bat' in brick_old['features']:
        if not brick_new['bat_charging'] == brick_old['bat_charging'] or not brick_new['bat_charging_standby'] == brick_old['bat_charging_standby']:
            bat_charging_store(brick_new['bat_charging'], brick_new['bat_charging_standby'], brick_new['_id'], brick_new['last_ts'], brick_new['desc'])
            bat_charging_send(brick_new['_id'], brick_new['bat_charging'], brick_new['bat_charging_standby'])
        if not brick_new['bat_charging'] and brick_old['bat_charging'] and not brick_new['bat_solar_charging']:
            brick_new['bat_periodic_voltage_request'] = 10
            result.append('request_bat_voltage')
        if not brick_new['bat_charging'] and brick_old['bat_charging'] and brick_new['bat_charging_standby'] and not brick_new['bat_solar_charging']:
            send_telegram('Charging finished on ' + (brick_new['_id'] if brick_new['desc'] is None or brick_new['desc'] == '' else brick_new['desc']))
        if not brick_new['bat_charging'] and not brick_new['bat_charging_standby'] and (brick_old['bat_charging'] or brick_old['bat_charging_standby']) and not brick_new['bat_solar_charging']:
            brick_new['bat_periodic_voltage_request'] = 10
            result.append('request_bat_voltage')
    return result


process = {
    't': __process_t,
    'h': __process_h,
    'b': __process_b,
    'l': __process_l,
    'y': __process_y
}


def process_exec(brick_new, brick_old, delivered_data):
    return [process[k](brick_new, brick_old) for k in delivered_data if k in process]
