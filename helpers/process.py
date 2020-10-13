from helpers.config import *
from datetime import datetime, timedelta

def __process_t(brick_new, brick_old):
    if 'temp' in brick_new['features'] and 'temp' in brick_old['features']:
        max_diff = 0
        for sensor in [sensor for sensor in brick_new['last_temps'] if sensor in brick_old['last_temps']]:
            diff = abs(brick_old['last_temps'][sensor] - brick_new['last_temps'][sensor])
            max_diff = diff if diff > max_diff else max_diff
        if 'bat' in brick_new['features'] and (brick_new['bat_charging'] or brick_new['bat_charging_standby']):  # If power-cord is connected delay can be 60
            brick_new['delay'] = 60
            brick_new['delay_increase_wait'] = 3
            return 'update_delay'
        elif max_diff > 0.25 and brick_new['delay'] > 60:  # TODO: eventuell abhaengig von presicion machen
            brick_new['delay'] = 60
            brick_new['delay_increase_wait'] = 3
            return 'update_delay'
        elif max_diff > 0.25:  # Wenn delay schon auf 60 ist muss kein update gesendet werden, da dies nur unnoetig rechenzeit braucht
            brick_new['delay_increase_wait'] = 3
            return None
        elif brick_new['delay_increase_wait'] <= 0 and brick_new['delay'] < 300:
            brick_new['delay'] += 60
            brick_new['delay_increase_wait'] = 3
            return 'update_delay'


def __process_b(brick_new, brick_old):
    if 'bat' in brick_new['features']:
        if brick_new['last_bat_reading'] < 3.5:
            send_telegram('Charge bat on ' + brick_new['id'] + ' (' + brick_new['desc'] + ') it reads ' + str(brick_new['last_bat_reading']) + ' Volts')


def __process_y(brick_new, brick_old):
    result = []
    if brick_new['initalized']:
        result.append('request_version')
        result.append('request_features')
        send_telegram('Brick ' + brick_new['id'] + ' (' + brick_new['desc'] + ') just started')
    if 'bat' in brick_new['features'] and 'bat_charging' in brick_old and 'bat_charging' in brick_new:
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
