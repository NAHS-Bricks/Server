import cherrypy
import json
import subprocess
import time
import os
import sys
import copy
from datetime import datetime, timedelta

if not (sys.version_info.major == 3 and sys.version_info.minor >= 4):
    raise Exception('At least Python3.4 required')

config = {'storagedir': '/tmp', 'statefile': 'state.json', 'server_port': 8081}
if os.path.isfile('config.json'):
    config.update(json.loads(open('config.json', 'r').read().strip()))
else:
    open('config.json', 'w').write(json.dumps(config, indent=2, sort_keys=True))
storagedir = config['storagedir'] if config['storagedir'].endswith('/') else config['storagedir'] + '/'
statefile = storagedir + config['statefile']

brick_state_defaults = {
    'all': {
        'id': None,
        'version': None,
        'features': [],
        'desc': '',
        'last_ts': None,
        'initalized': False
    },
    'temp': {
        'last_temps': {},
        'presicion': 11,
        'delay': 60,
        'delay_increase_wait': 3
    },
    'bat': {
        'last_bat_reading': 0,
        'last_bat_ts': None,
        'bat_charging': False,
        'bat_charging_standby': False
    }
}
bricks = {}
if os.path.isfile(statefile):
    bricks = json.loads(open(statefile, 'r').read().strip())


def __store_v(brick, value):
    brick['version'] = value


def __store_f(brick, value):
    for feature in [f for f in value if f not in brick['features']]:
        brick.update(brick_state_defaults[feature])
        brick['features'].append(feature)


def __store_t(brick, temps):
    if 'temp' not in brick['features']:
        return
    for sensor, temp in temps:
        storagefile = storagedir + brick['id'] + '_' + sensor + '.csv'
        entryline = str(brick['last_ts']) + ';' + str(temp) + '\n'
        open(storagefile, 'a').write(entryline)
        brick['last_temps'][sensor] = temp
    brick['delay_increase_wait'] -= (0 if brick['delay_increase_wait'] <= 0 else 1)


def __store_b(brick, voltage):
    if 'bat' not in brick['features']:
        return
    brick['last_bat_reading'] = voltage
    brick['last_bat_ts'] = brick['last_ts']


def __store_y(brick, bools):
    if 'bat' in brick['features']:
        brick['bat_charging'] = ('c' in bools)
        brick['bat_charging_standby'] = ('s' in bools)
    brick['initalized'] = ('i' in bools)


def __process_t(brick_new, brick_old):
    if 'temp' in brick_new['features'] and 'temp' in brick_old['features']:
        max_diff = 0
        for sensor in [sensor for sensor in brick_new['last_temps'] if sensor in brick_old['last_temps']]:
            diff = abs(brick_old['last_temps'][sensor] - brick_new['last_temps'][sensor])
            max_diff = diff if diff > max_diff else max_diff
        if max_diff > 0.25 and brick_new['delay'] > 60:  # TODO: eventuell abhaengig von presicion machen
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
            print('Charge bat on ' + brick_new['id'] + ' (' + brick_new['desc'] + ')')
            # TODO: send telegram message to charge bat


def __process_y(brick_new, brick_old):
    if brick_new['initalized']:
        return 'request_version_and_features'
    if 'bat' in brick_new['features'] and 'bat_charging' in brick_old and 'bat_charging' in brick_new:
        if not brick_new['bat_charging'] and brick_old['bat_charging']:
            return 'request_bat_voltage'
        if not brick_new['bat_charging'] and not brick_new['bat_charging_standby'] and (brick_old['bat_charging'] or brick_old['bat_charging_standby']):
            return 'request_bat_voltage'


def __feature_bat(brick):
    if brick['last_bat_ts']:
        if datetime.fromtimestamp(brick['last_ts']) > datetime.fromtimestamp(brick['last_bat_ts']) + timedelta(hours=12):
            return 'request_bat_voltage'
    else:
        return 'request_bat_voltage'


store = {
    'v': __store_v,
    'f': __store_f,
    't': __store_t,
    'b': __store_b,
    'y': __store_y
}

process = {
    't': __process_t,
    'b': __process_b,
    'y': __process_y
}

feature = {
    'bat': __feature_bat
}


def get_deviceid(ip):
    if ip == '127.0.0.1':
        return 'localhost'
    r = subprocess.check_output('cat /proc/net/arp | grep ' + str(ip), shell=True).decode('utf-8')
    return r.strip().split()[3].replace(':', '')


class Tempserver(object):
    """
    Input json keys:
    t = list of sensors with temps, where sensor and temp are lists themself (eg: [['s1', t1], ['s2', t2]] )
    v = bricks software version
    f = list of bricks features as in brick_state_defaults
    b = bat-voltage as float
    y = list of chars representing boolean values, if a char is in list it's considered as true if it's missing it's considered as false
        c = bat is charging
        s = bat charging is in standby
        i = brick initalized (just started up, runtimeData is on initial values)

    Output json keys:
    s = state is 0 for ok and 1 for failure
    d = delay value for brick to use
    p = precision for temp-sensors (int between 9 and 12)
    r = list of values, that are requestet from brick (as integers for easyer handling on brick)
        1 = version is requested
        2 = features are requested
        3 = bat-voltage is requested
    """
    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index(self):
        result = {'s': 0}
        if 'json' in dir(cherrypy.request):
            data = cherrypy.request.json
            print()
            print("Request: " + json.dumps(data))
            brick_ip = cherrypy.request.remote.ip
            brick_id = get_deviceid(brick_ip)
            if brick_id not in bricks:
                bricks[brick_id] = {}
                bricks[brick_id].update(brick_state_defaults['all'])
                bricks[brick_id]['id'] = brick_id

            # create intermediate brick for storing and processing current session
            brick = copy.deepcopy(bricks[brick_id])
            brick['last_ts'] = int(time.time())

            # storing stage -- just take data and store them to intermediate brick-element
            [store[k](brick, data[k]) for k in data if k in store]

            # processing stage -- compare new and old data and do calculations if nesseccary
            process_requests = [process[k](brick, bricks[brick_id]) for k in data if k in process]

            # feature-based processing stage
            feature_requests = [feature[k](brick) for k in brick['features'] if k in feature]

            for k in [k for k in process_requests + feature_requests if k]:
                if k == 'update_delay':
                    result['d'] = brick['delay']
                elif k == 'update_precision':  # Not used yet
                    result['p'] = brick['precision']
                elif k == 'request_bat_voltage':
                    if 'r' not in result:
                        result['r'] = []
                    result['r'].append(3)
                elif k == 'request_version_and_features':
                    if 'r' not in result:
                        result['r'] = []
                    result['r'].append(1)
                    result['r'].append(2)

            # save-back intermediate brick
            bricks[brick_id] = brick
            # and write statefile
            open(statefile, 'w').write(json.dumps(bricks, indent=2))
        print("Feedback: " + json.dumps(result))
        return result


if __name__ == '__main__':
    cherrypy.config.update({'server.socket_host': '0.0.0.0', 'server.socket_port': config['server_port'], })
    cherrypy.quickstart(Tempserver())
