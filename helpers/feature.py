from helpers.config import *
from datetime import datetime, timedelta


def __feature_bat(brick):
    if brick['last_bat_ts']:
        if datetime.fromtimestamp(brick['last_ts']) > datetime.fromtimestamp(brick['last_bat_ts']) + timedelta(hours=12):
            return 'request_bat_voltage'
    else:
        return 'request_bat_voltage'


def __feature_admin_override(brick):
    result = []
    if 'admin_override' in brick:
        if 'delay' in brick['admin_override']:
            brick['delay'] = brick['admin_override']['delay']
            brick['delay_increase_wait'] = 3
            result.append('update_delay')
        if 'bat' in brick['features'] and 'bat_voltage' in brick['admin_override'] and brick['admin_override']['bat_voltage']:
            result.append('request_bat_voltage')
        brick.pop('admin_override', None)
    brick['features'].remove('admin_override')
    return result


feature = {
    'bat': __feature_bat,
    'admin_override': __feature_admin_override
}
