import cherrypy
import json
import time
import os
import sys
import copy
from helpers.shared import config, send_telegram, get_deviceid
import helpers.shared
from helpers.store import store, brick_state_defaults
from helpers.process import process
from helpers.feature import feature

if not (sys.version_info.major == 3 and sys.version_info.minor >= 5):  # pragma: no cover
    raise Exception('At least Python3.5 required')


class Brickserver(object):
    """
    Input json keys:
    t = list of sensors with temps, where sensor and temp are lists themself (eg: [['s1', t1], ['s2', t2]] )
    c = list of sensors with corr, where sensor and corr are lists themself (eg: [['s1', c1], ['s2', c2]] )
    v = bricks software version (as string)
    f = list of bricks features as in brick_state_defaults
    b = bat-voltage as float
    y = list of chars representing boolean values, if a char is in list it's considered as true if it's missing it's considered as false
        c = bat is charging
        s = bat charging is in standby
        i = brick initalized (just started up, runtimeData is on initial values)

    Output json keys:
    s = state is 0 for ok and 1 for failure
    d = sleep_delay value for brick to use
    p = temp_precision for temp-sensors (int between 9 and 12)
    r = list of values, that are requestet from brick (as integers for easyer handling on brick)
        1 = version is requested
        2 = features are requested
        3 = bat-voltage is requested
        4 = temp-sensor correction values are requested
    """
    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index(self):
        test_suite = 'environment' in cherrypy.config and cherrypy.config['environment'] == 'test_suite'
        if test_suite:  # pragma: no cover
            if os.path.isfile(os.path.join(config['storagedir'], config['statefile'])):
                with open(os.path.join(config['storagedir'], config['statefile']), 'r') as f:
                    helpers.shared.bricks, helpers.shared.temp_sensors = json.loads(f.read().strip())
            else:
                helpers.shared.bricks = {}
                helpers.shared.temp_sensors = {}
            if os.path.isfile(os.path.join(config['storagedir'], 'telegram_messages')):
                os.remove(os.path.join(config['storagedir'], 'telegram_messages'))

        result = {'s': 0}
        if 'json' in dir(cherrypy.request):
            data = cherrypy.request.json
            if not test_suite:  # pragma: no cover
                print()
                print("Request: " + json.dumps(data))
            brick_ip = cherrypy.request.remote.ip
            brick_id = get_deviceid(brick_ip)
            if brick_id not in helpers.shared.bricks:
                helpers.shared.bricks[brick_id] = {}
                helpers.shared.bricks[brick_id].update(brick_state_defaults['all'])
                helpers.shared.bricks[brick_id]['id'] = brick_id

            # create intermediate brick for storing and processing current session
            brick = copy.deepcopy(helpers.shared.bricks[brick_id])
            brick['last_ts'] = int(time.time())

            # storing stage -- just take data and store them to intermediate brick-element
            [store[k](brick, data[k]) for k in data if k in store]

            # processing stage -- compare new and old data and do calculations if nesseccary
            process_requests = [process[k](brick, helpers.shared.bricks[brick_id]) for k in data if k in process]

            # feature-based processing stage
            feature_requests = [feature[k](brick) for k in brick['features'] if k in feature]

            """
            What the sollowing line does:
            Takes all entrys from process_requests + feature_requests and:
              - drops None elements
              - makes non list items to lists with one item aka if type(item) is not list return [item]
              - passes trough all lists
            this results in a list of lists, each of this lists is then unpacked in to one big list with all elements
            with the use of {} duplicate elements are removed
            """
            for k in {x for t in [(p if type(p) is list else [p]) for p in process_requests + feature_requests if p] for x in t}:
                if k.startswith('request_') and 'r' not in result:
                    result['r'] = []
                if k == 'update_sleep_delay':
                    result['d'] = brick['sleep_delay']
                elif k == 'update_temp_precision':
                    result['p'] = brick['temp_precision']
                elif k == 'request_bat_voltage':
                    result['r'].append(3)
                elif k == 'request_version':
                    result['r'].append(1)
                elif k == 'request_features':
                    result['r'].append(2)
                elif k == 'request_temp_corr':
                    result['r'].append(4)

            # save-back intermediate brick
            helpers.shared.bricks[brick_id] = brick
            # and write statefile
            with open(os.path.join(config['storagedir'], config['statefile']), 'w') as f:
                f.write(json.dumps([helpers.shared.bricks, helpers.shared.temp_sensors], indent=2))
        if not test_suite:  # pragma: no cover
            print("Feedback: " + json.dumps(result))
        return result

    """
    Admin interface to override some values
    Usable via set command:
      sleep_delay: integer (set delay to value)
      bat_voltage: bool (request_bat_voltage if true)
      desc: string (description of brick)
      temp_precision: integer (temperature sensors precision 9 <= value <= 12)
    """
    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def admin(self):
        test_suite = 'environment' in cherrypy.config and cherrypy.config['environment'] == 'test_suite'
        if test_suite:  # pragma: no cover
            if os.path.isfile(os.path.join(config['storagedir'], config['statefile'])):
                with open(os.path.join(config['storagedir'], config['statefile']), 'r') as f:
                    helpers.shared.bricks, helpers.shared.temp_sensors = json.loads(f.read().strip())
            else:
                helpers.shared.bricks = {}
                helpers.shared.temp_sensors = {}

        result = {'s': 0}
        if 'json' in dir(cherrypy.request):
            data = cherrypy.request.json
            if 'command' in data:
                command = data['command']
                if command == 'get_bricks':
                    result['bricks'] = []
                    for k in helpers.shared.bricks:
                        result['bricks'].append(k)
                elif command == 'get_brick' and 'brick' in data:
                    brick = data['brick']
                    if brick in helpers.shared.bricks:
                        result['brick'] = helpers.shared.bricks[brick]
                elif command == 'set' and 'brick' in data and 'key' in data and 'value' in data:
                    if data['brick'] in helpers.shared.bricks:
                        brick = helpers.shared.bricks[data['brick']]
                        if 'admin_override' not in brick['features']:
                            brick['features'].append('admin_override')
                        if 'admin_override' not in brick:
                            brick['admin_override'] = {}
                        if data['key'] == 'desc':
                            brick['desc'] = data['value']
                        elif data['key'] == 'temp_precision':
                            if data['value'] in range(9, 13) and 'temp' in brick['features']:
                                brick['temp_precision'] = data['value']
                                brick['admin_override'][data['key']] = True
                            else:
                                result['s'] = 5  # invalid value range(9, 12) or temp not in features
                        else:
                            brick['admin_override'][data['key']] = data['value']
                    else:
                        result['s'] = 1
                else:
                    result['s'] = 1
            else:
                result['s'] = 1
            with open(os.path.join(config['storagedir'], config['statefile']), 'w') as f:
                f.write(json.dumps([helpers.shared.bricks, helpers.shared.temp_sensors], indent=2))
        return result


if __name__ == '__main__':
    cherrypy.config.update({'server.socket_host': '0.0.0.0', 'server.socket_port': config['server_port'], })
    cherrypy.quickstart(Brickserver())
