import cherrypy
import json
import time
import os
import sys
import copy
import argparse
import tempfile
import zipfile
from datetime import datetime, timedelta
from cherrypy.lib import file_generator
from connector.mongodb import start_mongodb_connection, mongodb_lock_acquire, mongodb_lock_release, is_connected as mongodb_connected
from connector.mongodb import brick_get, brick_save, brick_all, brick_all_ids, util_get, util_save, latch_get, signal_all, signal_save
from connector.mongodb import brick_count, temp_sensor_count, humid_count, latch_count, signal_count, heater_count
from connector.mongodb import fwmetadata_save, fwmetadata_count, fwmetadata_latest, fanctl_count
from connector.mqtt import start_async_worker as start_mqtt_worker, is_connected as mqtt_connected, signal_send
from connector.influxdb import start_async_worker as start_influxdb_worker, is_connected as influxdb_connected
from connector.brick import start_async_worker as start_brick_worker
from connector.s3 import is_connected as s3_connected, firmware_save, firmware_get, firmware_exists, firmware_filename
from connector.ds import is_connected as ds_connected
from stage.store import store_exec as exec_store_stage
from stage.process import process_exec as exec_process_stage
from stage.feature import feature_exec as exec_feature_stage
from stage.feedback import feedback_exec as exec_feedback_stage
from helpers.current_version import current_brickserver_version
from helpers.shared import config, send_telegram, get_deviceid
from helpers.admin import admin_interface
from helpers.migrations import exec_migrate


if not (sys.version_info.major == 3 and sys.version_info.minor >= 6):  # pragma: no cover
    raise Exception('At least Python3.6 required')


class Brickserver(object):
    """
    Input json keys:
    a = adv5V value as int
    t = list of sensors with temps, where sensor and temp are lists themself (eg: [['s1', t1], ['s2', t2]] )
    c = list of sensors with corr (temperature), where sensor and corr are lists themself (eg: [['s1', c1], ['s2', c2]] )
    l = list of latch states, where the index of a state is the id of the latch input (eg: [0, 1] )
    h = list of sensors with humidity, where sensor and humid are lists themself (eg: [['s1', h1], ['s2', h2]] )
    k = list of sensors with corr (humidity), where sensor and corr are lists themself (eg: [['s1', c1], ['s2', c2]] )
    v = list of features with version (as float), where elements are lists themself, allways needs to contain os and all (as this are meta-features) (eg: [['os', 1.0], ['all', 1.0], ['bat', 1.0]] )
    f = list of bricks features as in brick_state_defaults
    b = bat-voltage as float
    y = list of chars representing boolean values, if a char is in list it's considered as true if it's missing it's considered as false
        c = bat is charging
        s = bat charging is in standby
        i = brick initalized (just started up, runtimeData is on initial values)
        d = delay_overwrite(AllwaysWithDefault) is active/set
        q = sleep_disabled is active/set
        w = Brick (with feature Bat) is connected to wall-power
    x = bricktype as int (1 = TempBrick)
    p = temp_precision for temp-sensors as int
    s = signal_count (number of signal outputs available on brick)
    d = delay_default value
    m = sketchMD5
    fs = fanctl fan-states. list of lists where first element of inner list is fanctl addr, second is state (0=Off, 1=On) and third is rps (eg: [[64, 0, 0], [65, 1, 12]])
    fm = fanctl fan-modes. list of lists where first element of inner list is fanctl addr and second is mode (-1-2) (eg: [[64, 0], [65, 1]])
    id = ident set during BrickSetup to identify Brick on first connection to Bricks-Server

    Output json keys:
    a = adv5V value for brick to use (int between 0 and 1023)
    s = state is 0 for ok and 1 for failure
    d = delay value for brick to use
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
        9 = humid-sensor correction values are requested
        10 = adc5V is requested
        11 = sketchMD5 is requested
        12 = otaUpdate is requested
        13 = fanctl fan-modes are requested
        14 = brick is requested to clear stored ident (to save space in FSmem)
    q = sets sleep_disabled (true or false)
    fm = fanctl fan-modes to be used. list of lists where first element of inner list is fanctl addr and second is mode (0-2) to set (eg: [[64, 0], [65, 1]])
    fd = fanctl fan-dutyCycle to be used. list of lists where first element of inner list is fanctl addr and second is dytyCycle (0-100) to set (eg: [[64, 0], [65, 100]])
    fs = fanctl fan-state to be used. list of lists where first element of inner list is fanctl addr and second is state (0=Off, 1=On) to set (eg: [[64, 0], [65, 1]])
    h = state of heater turned on (1) or off (0) (as int 0 or 1)
    """
    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index(self):
        test_suite = 'environment' in cherrypy.config and cherrypy.config['environment'] == 'test_suite'
        if test_suite:  # pragma: no cover
            if os.path.isfile('/tmp/telegram_messages'):
                os.remove('/tmp/telegram_messages')

        if cherrypy.request.method == "GET":
            health = {
                'version': current_brickserver_version,
                'mongodb_connected': mongodb_connected(),
                'influxdb_connected': influxdb_connected(),
                'mqtt_connected': mqtt_connected(),
                's3_connected': s3_connected(),
                'brick_count': brick_count(),
                'temp_sensor_count': temp_sensor_count(),
                'humid_sensor_count': humid_count(),
                'latch_count': latch_count(),
                'signal_count': signal_count(),
                'fwmetadata_count': fwmetadata_count(),
                'fanctl_count': fanctl_count(),
                'heater_count': heater_count(),
                'ds_allowed': config['allow']['ds'],
                'ds_connected': ds_connected() if config['allow']['ds'] else False
            }
            return health

        if 'json' in dir(cherrypy.request):
            data = cherrypy.request.json
            if not test_suite:  # pragma: no cover
                print()
                print("Deliver: " + json.dumps(data))
            brick_ip = cherrypy.request.remote.ip
            brick_id = get_deviceid(brick_ip)
            if test_suite and 'test_brick_id' in data:
                brick_id += str(int(data['test_brick_id']))

            # acquire lock on brick object and load it from db
            mongodb_lock_acquire(brick_id)
            brick_old = brick_get(brick_id)

            # create intermediate brick for storing and processing current session
            brick = copy.deepcopy(brick_old)
            brick['last_ts'] = int(time.time())
            brick['ip'] = brick_ip

            # ensure some structures are present in data with their defaults
            if 'y' not in data:
                data['y'] = list()

            # storing stage -- just take data and store them to intermediate brick-element
            exec_store_stage(brick, data)

            # processing stage -- compare new and old data and do calculations if nesseccary
            process_requests = exec_process_stage(brick, brick_old, data)

            # feature-based processing stage
            feature_requests = exec_feature_stage(brick)

            # feedback stage -- generates feedback to be send to brick
            feedback = exec_feedback_stage(brick, process_requests, feature_requests)

            # remove admin_override form brick if present (stages done, so it's no longer needed)
            brick['features'].pop('admin_override', None)
            brick.pop('admin_override', None)

            # save-back intermediate brick
            brick_save(brick)

            # release lock on brick object
            mongodb_lock_release(brick_id)

            if not test_suite:  # pragma: no cover
                print("Feedback: " + json.dumps(feedback))
            return feedback
        return {'s': 1}

    """
    Admin interface to override some values
    Usable via set command:
      delay: integer (set delay to value)
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
            if not test_suite:  # pragma: no cover
                print("Admin: " + json.dumps(data))
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

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def upload(self, firmware=None):
        if firmware is not None:
            size = 0
            with tempfile.TemporaryFile() as tmp_file:
                while True:
                    data = firmware.file.read(8192)
                    if not data:
                        break
                    tmp_file.write(data)
                    size += len(data)
                    if size > 2097152:
                        return {'s': 2, 'm': 'file size is to big'}
                tmp_file.seek(0)
                with zipfile.ZipFile(tmp_file, 'r') as zip_file:
                    if 'metadata.json' not in zip_file.namelist():
                        return {'s': 3, 'm': 'metadata.json is missing in firmware package'}
                    if 'firmware.bin' not in zip_file.namelist():
                        return {'s': 4, 'm': 'firmware.bin is missing in firmware package'}
                    try:
                        metadata = json.loads(zip_file.read('metadata.json').decode('utf-8'))
                    except Exception:
                        return {'s': 9, 'm': 'metadata.json is not a valid json file'}
                    if 'brick_type' not in metadata:
                        return {'s': 5, 'm': 'brick_type missing in metadata'}
                    if 'version' not in metadata:
                        return {'s': 6, 'm': 'version missing in metadata'}
                    if 'sketchMD5' not in metadata:
                        return {'s': 7, 'm': 'sketchMD5 missing in metadata'}
                    if 'content' not in metadata:
                        return {'s': 8, 'm': 'content missing in metadata'}
                    fwmetadata_save(metadata)
                    firmware_save(zip_file.open('firmware.bin'), fwmetadata=metadata)
        else:
            return {'s': 1, 'm': 'missing firmware package'}
        return {'s': 0}

    @cherrypy.expose
    def ota(self):
        brick_ip = cherrypy.request.remote.ip
        brick_id = get_deviceid(brick_ip)

        # acquire lock on brick object and load it from db
        mongodb_lock_acquire(brick_id)
        brick = brick_get(brick_id)

        fwm = fwmetadata_latest(brick['type'])

        if 'os' in brick['features'] and brick['features']['os'] >= 1.01:
            if fwm is not None and (brick['sketchMD5'] is None or not brick['sketchMD5'] == fwm['sketchMD5']) and firmware_exists(fwmetadata=fwm):
                brick['otaUpdate'] = 'running'
            else:
                brick['otaUpdate'] = 'skipped'

            brick_save(brick)

        # release lock on brick object
        mongodb_lock_release(brick_id)

        if 'otaUpdate' in brick and brick['otaUpdate'] == 'running':
            cherrypy.response.headers['Content-Type'] = "application/octet-stream"
            cherrypy.response.headers['Content-Disposition'] = 'attachment; filename="' + firmware_filename(fwmetadata=fwm) + '"'
            cherrypy.response.headers['x-MD5'] = fwm['sketchMD5']
            return file_generator(firmware_get(fwmetadata=fwm))
        else:
            cherrypy.response.status = 304
            return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="NAHS-BrickServer")
    parser.add_argument('--version', '-v', dest='version', action='store_true', help='Prints version of BrickServer')
    parser.add_argument('--migrate', '-m', dest='migrate', action='store_true', help='Executes migrations')
    args = parser.parse_args()

    if args.version:
        print(current_brickserver_version)
        sys.exit(0)

    if args.migrate:
        start_mongodb_connection()
        exec_migrate(current_brickserver_version)
        sys.exit(0)

    start_mqtt_worker()
    start_influxdb_worker()
    start_brick_worker()
    start_mongodb_connection()
    cherrypy.config.update({'server.socket_host': '0.0.0.0', 'server.socket_port': config['server_port'], })
    cherrypy.quickstart(Brickserver())
