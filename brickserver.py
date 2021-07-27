import cherrypy
import json
import time
import os
import sys
import copy
import argparse
from datetime import datetime, timedelta
from connector.mongodb import brick_get, brick_save, brick_all, brick_all_ids, util_get, util_save, latch_get, signal_all, signal_save
from connector.rabbitmq import event_create
from stage.store import store as store_stage
from stage.process import process as process_stage
from stage.feature import feature as feature_stage
from event.worker import start_thread as event_worker
from helpers.current_version import current_brickserver_version
from helpers.shared import config, send_telegram, get_deviceid
from helpers.admin import admin_interface
from helpers.migrations import exec_migrate


if not (sys.version_info.major == 3 and sys.version_info.minor >= 6):  # pragma: no cover
    raise Exception('At least Python3.6 required')


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
        d = allwaysOverwriteDelay(WithDefault) is active/set
        q = sleep_disabled is active/set
    x = bricktype as int (1 = TempBrick)
    p = temp_precision for temp-sensors as int
    s = signal_count (number of signal outputs available on brick)
    d = delay_default value

    Output json keys:
    s = state is 0 for ok and 1 for failure
    d = sleep_delay value for brick to use
    p = temp_precision for temp-sensors (int between 9 and 12)
    t = list of lists where the index of the outerlist is the latch id and the nested lists carry the triggers to enable (eg: [[0, 2], [1, 3]])
    o = list of signal output states where 0 is output off (low) and 1 is output on (high) length of list equals signal_count
    r = list of values, that are requested from brick (as integers for easier handling on brick)
        1 = features/versions are requested
        3 = bat-voltage is requested
        4 = temp-sensor correction values are requested
        5 = brick-type is requested
        6 = temp_precision is requested
        7 = signal_count is requested
        8 = delay_default is requested
    q = sets sleep_disabled (true or false)
    """
    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index(self):
        test_suite = 'environment' in cherrypy.config and cherrypy.config['environment'] == 'test_suite'
        if test_suite:  # pragma: no cover
            if os.path.isfile('/tmp/telegram_messages'):
                os.remove('/tmp/telegram_messages')

        result = {'s': 0}
        if 'json' in dir(cherrypy.request):
            data = cherrypy.request.json
            if not test_suite:  # pragma: no cover
                print()
                print("Deliver: " + json.dumps(data))
            brick_ip = cherrypy.request.remote.ip
            brick_id = get_deviceid(brick_ip)
            if test_suite and 'test_brick_id' in data:
                brick_id += str(int(data['test_brick_id']))
            brick_old = brick_get(brick_id)

            # create intermediate brick for storing and processing current session
            brick = copy.deepcopy(brick_old)
            brick['last_ts'] = int(time.time())
            brick['ip'] = brick_ip

            # ensure some structures are present in data with their defaults
            if 'y' not in data:
                data['y'] = list()

            # storing stage -- just take data and store them to intermediate brick-element
            [store_stage[k](brick, data[k]) for k in data if k in store_stage]

            # processing stage -- compare new and old data and do calculations if nesseccary
            process_requests = [process_stage[k](brick, brick_old) for k in data if k in process_stage]

            # feature-based processing stage
            feature_requests = [feature_stage[k](brick) for k in brick['features'] if k in feature_stage]

            """
            What the following line does:
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
                    result['t'] = list()
                    for i in range(0, brick['latch_count']):
                        result['t'].append(sorted(latch_get(brick['_id'], i)['triggers']))
                elif k == 'update_signal_states':
                    result['o'] = list()
                    for signal in signal_all(brick['_id']):
                        result['o'].append(signal['state'])
                        if signal['state_transmitted_ts'] is None:
                            signal['state_transmitted_ts'] = brick['last_ts']
                            signal_save(signal)
                elif k == 'request_versions':
                    result['r'].append(1)
                elif k == 'request_bat_voltage':
                    result['r'].append(3)
                elif k == 'request_temp_corr':
                    result['r'].append(4)
                elif k == 'request_type':
                    result['r'].append(5)
                elif k == 'request_temp_precision':
                    result['r'].append(6)
                elif k == 'request_signal_count':
                    result['r'].append(7)

            # special-case: feature sleep is present and requests are made: override delay to 10 -- except admin_override for sleep_delay is present
            if 'sleep' in brick['features'] and 'r' in result and ('admin_override' not in brick or 'sleep_delay' not in brick['admin_override']):
                brick['sleep_delay'] = 10
                result['d'] = 10

            # remove admin_override form brick if present (processing done, so it's no longer needed)
            brick['features'].pop('admin_override', None)
            brick.pop('admin_override', None)

            # save-back intermediate brick
            brick_save(brick)

            # create an event for this brick
            event_create(brick)
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

        if 'json' in dir(cherrypy.request):
            data = cherrypy.request.json
            return admin_interface(data)
        else:
            return {'s': 99}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def cron(self):
        test_suite = 'environment' in cherrypy.config and cherrypy.config['environment'] == 'test_suite'
        if test_suite:  # pragma: no cover
            if os.path.isfile('/tmp/telegram_messages'):
                os.remove('/tmp/telegram_messages')

        dt_now = datetime.now()
        ts_3_minutes_ago = int(datetime.timestamp(dt_now - timedelta(minutes=3)))
        ts_1_hour_ago = int(datetime.timestamp(dt_now - timedelta(hours=1)))
        ts_now = int(datetime.timestamp(dt_now))
        cron_data = util_get('cron_data')
        if 'offline_send' not in cron_data:
            cron_data['offline_send'] = {}

        if 'last_ts' not in cron_data or cron_data['last_ts'] < ts_3_minutes_ago:
            for brick in brick_all_ids():
                cron_data['offline_send'][brick] = True
        else:
            for brick in [brick for brick in brick_all_ids() if brick not in cron_data['offline_send']]:
                cron_data['offline_send'][brick] = True

        for brick in [brick for brick in brick_all() if brick['last_ts']]:
            if brick['last_ts'] > ts_1_hour_ago:  # Has send data within the last hour
                cron_data['offline_send'][brick['_id']] = False
            elif not cron_data['offline_send'][brick['_id']]:  # One hour offline and no message send
                send_telegram("Brick " + (brick['_id'] if brick['desc'] is None or brick['desc'] == '' else brick['desc']) + " didn't send any data within the last hour!")
                cron_data['offline_send'][brick['_id']] = True

        # Create daily report
        if dt_now.hour == 20:
            if 'last_report_ts' not in cron_data or not datetime.fromtimestamp(cron_data['last_report_ts']).day == dt_now.day:
                message = 'Daily-Report:\n\n'
                min_bat_val, min_bat_str = (6, None)
                low_prediction = list()
                for brick in [brick for brick in brick_all() if 'bat' in brick['features']]:
                    if brick['bat_last_reading'] < min_bat_val:
                        min_bat_val = brick['bat_last_reading']
                        min_bat_str = (brick['_id'] if brick['desc'] is None or brick['desc'] == '' else brick['desc'])
                    if brick['bat_runtime_prediction'] is not None and int(brick['bat_runtime_prediction']) <= 14:
                        brick_str = (brick['_id'] if brick['desc'] is None or brick['desc'] == '' else brick['desc'])
                        low_prediction.append((int(brick['bat_runtime_prediction']), brick_str))
                message += 'Lowest Bat: ' + str(round(min_bat_val, 3)) + ' at ' + str(min_bat_str) + '\n'
                if len(low_prediction) == 0:
                    message += 'No Bricks predicted to be empty within 14 days.'
                else:
                    # bubble sort the list from low to high
                    for i in range(0, len(low_prediction) - 1):  # pragma: no cover
                        for j in range(i + 1, len(low_prediction)):
                            if low_prediction[i][0] > low_prediction[j][0]:
                                stat = low_prediction[i]
                                low_prediction[i] = low_prediction[j]
                                low_prediction[j] = stat
                    message += 'Bricks predicted to be empty within 14 days:\n'
                    for predict, brick_str in low_prediction:
                        message += f'{brick_str} in {predict} days\n'
                send_telegram(message)
                cron_data['last_report_ts'] = ts_now

        cron_data['last_ts'] = ts_now
        util_save(cron_data)
        return {'s': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="NAHS-BrickServer")
    parser.add_argument('--version', '-v', dest='version', action='store_true', help='Prints version of BrickServer')
    parser.add_argument('--migrate', '-m', dest='migrate', action='store_true', help='Executes migrations')
    args = parser.parse_args()

    if args.version:
        print(current_brickserver_version)
        sys.exit(0)

    if args.migrate:
        exec_migrate(current_brickserver_version)
        sys.exit(0)

    event_worker()

    cherrypy.config.update({'server.socket_host': '0.0.0.0', 'server.socket_port': config['server_port'], })
    cherrypy.quickstart(Brickserver())
