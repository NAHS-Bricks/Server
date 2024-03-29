from connector.mongodb import temp_sensor_get, humid_get, signal_all, fanctl_all, heater_get
from datetime import datetime, timedelta


def __feature_os(brick):
    result = list()
    if brick['features']['os'] >= 1.01:
        if 'otaUpdate' in brick:
            if brick['otaUpdate'] == 'requested':
                result.append('request_otaUpdate')
            elif brick['initalized']:
                brick['otaUpdate'] = 'done'
            else:
                brick.pop('otaUpdate', None)
        if brick.get('sketchMD5') is None and not brick['initalized']:
            result.append('request_sketchMD5')
        if brick['initalized']:
            brick['sketchMD5'] = None
    return result


def __feature_all(brick):
    result = list()
    if brick['features']['all'] >= 1.02 and brick['delay_default'] is None:
        result.append('request_delay_default')
    if brick['features']['all'] >= 1.02 and brick['delay_overwrite']:
        brick['delay'] = (brick['delay_default'] if brick['delay_default'] is not None else 60)
    else:
        if 'sleep' not in brick['features'] and brick['features']['all'] >= 1.02:
            if brick['delay_default'] is not None and not brick['delay'] == brick['delay_default']:
                brick['delay'] = brick['delay_default']
                result.append('update_delay')
    return result


def __feature_bat(brick):
    result = list()
    if brick['bat_last_ts']:
        dt_now = datetime.fromtimestamp(brick['last_ts'])
        dt_last = datetime.fromtimestamp(brick['bat_last_ts'])
        if (dt_last.hour % 12) == 7:
            # align to half past 7
            if dt_now >= (dt_last + timedelta(hours=12)).replace(minute=30, second=0):
                result.append('request_bat_voltage')
        elif (dt_last.hour % 12) in range(1, 7):
            # expand the time a bit
            if dt_now >= dt_last + timedelta(hours=12.5):
                result.append('request_bat_voltage')
        else:
            # shorten the time a bit
            if dt_now >= dt_last + timedelta(hours=11.5):
                result.append('request_bat_voltage')
    else:
        result.append('request_bat_voltage')

    if brick['features']['bat'] >= 1.01 and brick.get('bat_adc5V') is None:
        result.append('request_bat_adc5V')
    return result


def __feature_sleep(brick):
    if brick['features']['all'] >= 1.02 and brick['delay_overwrite']:
        return
    result = list()
    prefered_delay = list()
    brick['sleep_increase_wait'] -= (0 if brick['sleep_increase_wait'] <= 0 else 1)
    # If power-cord is connected delay can be set to 60, except it's solar charged
    if 'bat' in brick['features'] and (brick['bat_charging'] or brick['bat_charging_standby']) and not brick['bat_solar_charging']:
        prefered_delay.append(60)
        brick['sleep_increase_wait'] = 3
    if 'temp' in brick['features'] or 'humid' in brick['features']:
        if ('temp' in brick['features'] and brick['temp_max_diff'] > 0.25) or ('humid' in brick['features'] and brick['humid_max_diff'] > 0.25) or brick['delay'] < 60:
            prefered_delay.append(60)
            brick['sleep_increase_wait'] = 3
        elif brick['sleep_increase_wait'] <= 0 and brick['delay'] < 300:
            prefered_delay.append(brick['delay'] + 60)
            brick['sleep_increase_wait'] = 3
        else:
            prefered_delay.append(min(brick['delay'], 300))
    if 'latch' in brick['features']:
        if brick['latch_triggerstate_received']:
            prefered_delay.append(20)
        else:
            prefered_delay.append(900)
    if 'signal' in brick['features']:
        for signal in signal_all(brick['_id']):
            if signal['state'] == 1:  # if at least one signal is going to be switched on, set delay to 60
                prefered_delay.append(60)
                break
        else:
            prefered_delay.append(120)
    if 'heat' in brick['features']:
        if heater_get(brick['_id'])['state'] == 1:
            prefered_delay.append(60)
        else:
            prefered_delay.append(120)
    if brick['features']['sleep'] >= 1.01 and brick['sleep_set_disabled'] is not None and not brick['sleep_disabled'] == brick['sleep_set_disabled']:
        prefered_delay.append(10)
        result.append('update_sleep_disabled')

    if len(prefered_delay) > 0:
        delay = sorted(prefered_delay)[0]
        if not delay == brick['delay']:
            brick['delay'] = delay
            result.append('update_delay')
    elif brick['features']['all'] >= 1.02 and brick['delay_default'] is not None and not brick['delay'] == brick['delay_default']:
        brick['delay'] = brick['delay_default']
        result.append('update_delay')
    return result


def __feature_temp(brick):
    result = []
    for sensor in [temp_sensor_get(sensor) for sensor in brick['temp_sensors']]:
        if sensor['corr'] is None:
            result.append('request_temp_corr')
            break
    if brick['temp_precision'] is None:
        result.append('request_temp_precision')
    return result


def __feature_humid(brick):
    for sensor in [humid_get(sensor) for sensor in brick['humid_sensors']]:
        if sensor['corr'] is None:
            return 'request_humid_corr'


def __feature_signal(brick):
    if brick['signal_count'] is None:
        return 'request_signal_count'


def __feature_fanctl(brick):
    result = list()
    for fanctl in fanctl_all(brick['_id']):
        if not fanctl['last_ts'] == brick['last_ts']:
            continue
        if fanctl['mode'] is None and 'request_fanctl_mode' not in result:
            result.append('request_fanctl_mode')
        if fanctl['mode'] is not None and fanctl['mode_transmitted_ts'] is None and 'update_fanctl_mode' not in result:
            result.append('update_fanctl_mode')
        if fanctl['mode'] is not None and fanctl['mode'] > -1:
            if fanctl['dutyCycle_transmitted_ts'] is None and fanctl['dutyCycle'] is not None and 'update_fanctl_duty' not in result:
                result.append('update_fanctl_duty')
            if fanctl['state_should'] is not None and not fanctl['state_should'] == fanctl['state']:
                if fanctl['state_should'] == 1 and fanctl['dutyCycle'] is not None:
                    if 'update_fanctl_duty' not in result:
                        result.append('update_fanctl_duty')
                elif 'update_fanctl_state' not in result:
                    result.append('update_fanctl_state')
    return result


def __feature_admin_override(brick):
    result = []
    if 'admin_override' not in brick:  # pragma: no cover
        return result
    if 'delay' in brick['admin_override'] and not (brick['features']['all'] >= 1.02 and brick['delay_overwrite']):
        brick['delay'] = brick['admin_override']['delay']
        brick['sleep_increase_wait'] = 3
        result.append('update_delay')
    if 'bat' in brick['features']:
        if 'bat_voltage' in brick['admin_override'] and brick['admin_override']['bat_voltage']:
            result.append('request_bat_voltage')
        if 'bat_adc5V' in brick['admin_override']:
            result.append('update_bat_adc5V')
            result.append('request_bat_voltage')
    if 'temp' in brick['features'] and 'temp_precision' in brick['admin_override']:
        result.append('update_temp_precision')
    if 'latch' in brick['features'] and 'latch_triggers' in brick['admin_override']:
        result.append('update_latch_triggers')
    if 'signal' in brick['features'] and 'signal_states' in brick['admin_override']:
        result.append('update_signal_states')
    if 'heat' in brick['features']:
        if 'temp_precision' in brick['admin_override']:
            result.append('update_temp_precision')
        if 'heater_state' in brick['admin_override']:
            result.append('update_heater_state')
    return result


feature = {
    'os': __feature_os,
    'all': __feature_all,
    'bat': __feature_bat,
    'sleep': __feature_sleep,
    'temp': __feature_temp,
    'heat': __feature_temp,
    'humid': __feature_humid,
    'signal': __feature_signal,
    'fanctl': __feature_fanctl,
    'admin_override': __feature_admin_override
}


def feature_exec(brick):
    return [feature[k](brick) for k in brick['features'] if k in feature]
