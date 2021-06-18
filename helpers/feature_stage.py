from helpers.mongodb import temp_sensor_get, signal_all
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
        if (brick['temp_max_diff'] > 0.25 and brick['sleep_delay'] > 60) or brick['sleep_delay'] < 60:
            brick['sleep_delay'] = 60
            brick['sleep_increase_wait'] = 3
            return 'update_sleep_delay'
        elif brick['temp_max_diff'] > 0.25:  # If sleep_delay is allready 60 we don't need to send an update
            brick['sleep_increase_wait'] = 3
            return None
        elif brick['sleep_increase_wait'] <= 0 and brick['sleep_delay'] < 300:
            brick['sleep_delay'] += 60
            brick['sleep_increase_wait'] = 3
            return 'update_sleep_delay'
    elif 'latch' in brick['features']:
        if brick['latch_triggerstate_received']:
            brick['sleep_delay'] = 20
        else:
            brick['sleep_delay'] = 900
        return 'update_sleep_delay'
    elif 'signal' in brick['features']:
        for signal in signal_all(brick['_id']):
            if signal['state'] == 1:  # if at least one signal is going to be switched on, set sleep_delay to 60
                brick['sleep_delay'] = 60
                break
        else:
            brick['sleep_delay'] = 120  # otherwise set is to 120
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


def __feature_signal(brick):
    if brick['signal_count'] is None:
        return 'request_signal_count'


def __feature_admin_override(brick):
    result = []
    if 'admin_override' not in brick:  # pragma: no cover
        return result
    if 'sleep_delay' in brick['admin_override']:
        brick['sleep_delay'] = brick['admin_override']['sleep_delay']
        brick['sleep_increase_wait'] = 3
        result.append('update_sleep_delay')
    if 'bat' in brick['features'] and 'bat_voltage' in brick['admin_override'] and brick['admin_override']['bat_voltage']:
        result.append('request_bat_voltage')
    if 'temp' in brick['features'] and 'temp_precision' in brick['admin_override']:
        result.append('update_temp_precision')
    if 'latch' in brick['features'] and 'latch_triggers' in brick['admin_override']:
        result.append('update_latch_triggers')
    if 'signal' in brick['features'] and 'signal_states' in brick['admin_override']:
        result.append('update_signal_states')
    return result


feature = {
    'bat': __feature_bat,
    'sleep': __feature_sleep,
    'temp': __feature_temp,
    'signal': __feature_signal,
    'admin_override': __feature_admin_override
}
