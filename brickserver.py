import cherrypy
import json
import time
import os
import sys
import copy
from datetime import datetime, timedelta
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
    l = list of latch states, where the index of a state is the id of the latch input (eg: [0, 1] )
    c = list of sensors with corr, where sensor and corr are lists themself (eg: [['s1', c1], ['s2', c2]] )
    v = list of features with version (as float), where elements are lists themself, allways needs to contain os and all (as this are meta-features) (eg: [['os', 1.0], ['all', 1.0], ['bat', 1.0]] )
    f = list of bricks features as in brick_state_defaults
    b = bat-voltage as float
    y = list of chars representing boolean values, if a char is in list it's considered as true if it's missing it's considered as false
        c = bat is charging
        s = bat charging is in standby
        i = brick initalized (just started up, runtimeData is on initial values)
    x = bricktype as int (1 = TempBrick)
    p = temp_precision for temp-sensors as int

    Output json keys:
    s = state is 0 for ok and 1 for failure
    d = sleep_delay value for brick to use
    p = temp_precision for temp-sensors (int between 9 and 12)
    r = list of values, that are requestet from brick (as integers for easier handling on brick)
        1 = version is requested
        2 = features are requested
        3 = bat-voltage is requested
        4 = temp-sensor correction values are requested
        5 = brick-type is requested
        6 = temp_precision is requested
    t = list of lists where the index of the outerlist is the latch id and the nested lists carry the triggers to enable (eg: [[0, 2], [1, 3]])
    """
    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index(self):
        test_suite = 'environment' in cherrypy.config and cherrypy.config['environment'] == 'test_suite'
        if test_suite:  # pragma: no cover
            helpers.shared.state_load()
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
                elif k == 'update_latch_triggers':
                    result['t'] = brick['latch_triggers']
                elif k == 'request_version':
                    result['r'].append(1)
                elif k == 'request_features':
                    result['r'].append(2)
                elif k == 'request_bat_voltage':
                    result['r'].append(3)
                elif k == 'request_temp_corr':
                    result['r'].append(4)
                elif k == 'request_type':
                    result['r'].append(5)
                elif k == 'request_temp_precision':
                    result['r'].append(6)

            # save-back intermediate brick
            helpers.shared.bricks[brick_id] = brick
            # and write statefile
            helpers.shared.state_save()
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
            helpers.shared.state_load()

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
                                result['s'] = 4  # invalid value range(9, 12) or temp not in features
                        else:
                            brick['admin_override'][data['key']] = data['value']
                    else:
                        result['s'] = 3  # Invalid Brick
                else:
                    result['s'] = 2  # Unknown, invalid or incomplete command
            else:
                result['s'] = 1  # Command missing in data
            helpers.shared.state_save()
        return result

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def cron(self):
        test_suite = 'environment' in cherrypy.config and cherrypy.config['environment'] == 'test_suite'
        if test_suite:  # pragma: no cover
            helpers.shared.state_load()
            if os.path.isfile(os.path.join(config['storagedir'], 'telegram_messages')):
                os.remove(os.path.join(config['storagedir'], 'telegram_messages'))

        dt_now = datetime.now()
        ts_3_minutes_ago = int(datetime.timestamp(dt_now - timedelta(minutes=3)))
        ts_1_hour_ago = int(datetime.timestamp(dt_now - timedelta(hours=1)))
        ts_now = int(datetime.timestamp(dt_now))
        if 'offline_send' not in helpers.shared.cron_data:
            helpers.shared.cron_data['offline_send'] = {}

        if 'last_ts' not in helpers.shared.cron_data or helpers.shared.cron_data['last_ts'] < ts_3_minutes_ago:
            for brick in helpers.shared.bricks:
                helpers.shared.cron_data['offline_send'][brick] = True
        else:
            for brick in [brick for brick in helpers.shared.bricks if brick not in helpers.shared.cron_data['offline_send']]:
                helpers.shared.cron_data['offline_send'][brick] = True

        for brick in [brick for brick in helpers.shared.bricks if helpers.shared.bricks[brick]['last_ts']]:
            if helpers.shared.bricks[brick]['last_ts'] > ts_1_hour_ago:  # Has send data within the last hour
                helpers.shared.cron_data['offline_send'][brick] = False
            elif not helpers.shared.cron_data['offline_send'][brick]:  # One hour offline and no message send
                send_telegram("Brick " + brick + " (" + helpers.shared.bricks[brick]['desc'] + ") didn't send any data within the last hour!")
                helpers.shared.cron_data['offline_send'][brick] = True

        # Create dayly report
        if dt_now.hour == 20:
            if 'last_report_ts' not in helpers.shared.cron_data or not datetime.fromtimestamp(helpers.shared.cron_data['last_report_ts']).day == dt_now.day:
                message = 'Dayly-Report:\n\n'
                max_bat_val, max_bat_brick, max_bat_desc = (0, None, None)
                min_bat_val, min_bat_brick, min_bat_desc = (6, None, None)
                for brick in [helpers.shared.bricks[brick_id] for brick_id in helpers.shared.bricks if 'bat' in helpers.shared.bricks[brick_id]['features']]:
                    if brick['bat_last_ts'] is None:
                        continue
                    if brick['bat_last_reading'] < min_bat_val:
                        min_bat_val = brick['bat_last_reading']
                        min_bat_brick = brick['id']
                        min_bat_desc = brick['desc']
                    if brick['bat_last_reading'] > max_bat_val:
                        max_bat_val = brick['bat_last_reading']
                        max_bat_brick = brick['id']
                        max_bat_desc = brick['desc']
                message += 'Lowest Bat: ' + str(min_bat_val) + ' at ' + str(min_bat_brick) + '(' + str(min_bat_desc) + ')\n'
                message += 'Highest Bat: ' + str(max_bat_val) + ' at ' + str(max_bat_brick) + '(' + str(max_bat_desc) + ')'
                send_telegram(message)
                helpers.shared.cron_data['last_report_ts'] = ts_now

        helpers.shared.cron_data['last_ts'] = ts_now
        helpers.shared.state_save()
        return {'s': 0}


if __name__ == '__main__':
    cherrypy.config.update({'server.socket_host': '0.0.0.0', 'server.socket_port': config['server_port'], })
    cherrypy.quickstart(Brickserver())
