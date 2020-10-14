from helpers.config import *
from datetime import datetime, timedelta


def __feature_bat(brick):
    if brick['last_bat_ts']:
        if datetime.fromtimestamp(brick['last_ts']) > datetime.fromtimestamp(brick['last_bat_ts']) + timedelta(hours=12):
            return 'request_bat_voltage'
    else:
        return 'request_bat_voltage'


def __feature_sleep(brick):
    brick['delay_increase_wait'] -= (0 if brick['delay_increase_wait'] <= 0 else 1)
    # If power-cord is connected delay can be set to 60
    if 'bat' in brick['features'] and (brick['bat_charging'] or brick['bat_charging_standby']):
        brick['delay'] = 60
        brick['delay_increase_wait'] = 3
        return 'update_delay'
    elif 'temp' in brick['features']:
        if brick['max_temp_diff'] > 0.25 and brick['delay'] > 60:  # TODO: eventuell abhaengig von precision machen
            brick['delay'] = 60
            brick['delay_increase_wait'] = 3
            return 'update_delay'
        # If delay is allready 60 we don't need to send an update, as this just consumes processing power
        elif brick['max_temp_diff'] > 0.25:
            brick['delay_increase_wait'] = 3
            return None
        elif brick['delay_increase_wait'] <= 0 and brick['delay'] < 300:
            brick['delay'] += 60
            brick['delay_increase_wait'] = 3
            return 'update_delay'


def __feature_admin_override(brick):
    result = []
    if 'admin_override' in brick:
        if 'delay' in brick['admin_override']:
            brick['delay'] = brick['admin_override']['delay']
            brick['delay_increase_wait'] = 3
            result.append('update_delay')
        if 'bat' in brick['features'] and 'bat_voltage' in brick['admin_override'] and brick['admin_override']['bat_voltage']:
            result.append('request_bat_voltage')
        if 'temp' in brick['features'] and 'precision' in brick['admin_override']:
            result.append('update_precision')
        brick.pop('admin_override', None)
    brick['features'].remove('admin_override')
    return result


feature = {
    'bat': __feature_bat,
    'sleep': __feature_sleep,
    'admin_override': __feature_admin_override
}
