from helpers.mongodb import temp_sensor_get
from datetime import datetime, timedelta


def __feature_bat(brick):
    if brick['bat_last_ts']:
        if datetime.fromtimestamp(brick['last_ts']) > datetime.fromtimestamp(brick['bat_last_ts']) + timedelta(hours=12):
            return 'request_bat_voltage'
    else:
        return 'request_bat_voltage'


def __feature_sleep(brick):
    brick['sleep_increase_wait'] -= (0 if brick['sleep_increase_wait'] <= 0 else 1)
    # If power-cord is connected sleep_delay can be set to 60
    if 'bat' in brick['features'] and (brick['bat_charging'] or brick['bat_charging_standby']):
        brick['sleep_delay'] = 60
        brick['sleep_increase_wait'] = 3
        return 'update_sleep_delay'
    elif 'temp' in brick['features']:
        if brick['temp_max_diff'] > 0.25 and brick['sleep_delay'] > 60:  # TODO: eventuell abhaengig von temp_precision machen
            brick['sleep_delay'] = 60
            brick['sleep_increase_wait'] = 3
            return 'update_sleep_delay'
        # If sleep_delay is allready 60 we don't need to send an update, as this just consumes processing power
        elif brick['temp_max_diff'] > 0.25:
            brick['sleep_increase_wait'] = 3
            return None
        elif brick['sleep_increase_wait'] <= 0 and brick['sleep_delay'] < 300:
            brick['sleep_delay'] += 60
            brick['sleep_increase_wait'] = 3
            return 'update_sleep_delay'


def __feature_temp(brick):
    result = []
    for sensor in [temp_sensor_get(sensor) for sensor in brick['temp_sensors']]:
        if sensor['corr'] is None:
            result.append('request_temp_corr')
            break
    if brick['temp_precision'] is None:
        result.append('request_temp_precision')
    return result


def __feature_admin_override(brick):
    result = []
    if 'admin_override' in brick:
        if 'sleep_delay' in brick['admin_override']:
            brick['sleep_delay'] = brick['admin_override']['sleep_delay']
            brick['sleep_increase_wait'] = 3
            result.append('update_sleep_delay')
        if 'bat' in brick['features'] and 'bat_voltage' in brick['admin_override'] and brick['admin_override']['bat_voltage']:
            result.append('request_bat_voltage')
        if 'temp' in brick['features'] and 'temp_precision' in brick['admin_override']:
            result.append('update_temp_precision')
        brick.pop('admin_override', None)
    return result


feature = {
    'bat': __feature_bat,
    'sleep': __feature_sleep,
    'temp': __feature_temp,
    'admin_override': __feature_admin_override
}
