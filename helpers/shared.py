import os
import json
import subprocess
import cherrypy
from datetime import datetime, timedelta


config = {
    'server_port': 8081,
    'telegram_cmd': None,
    'mongo': {
        'server': 'localhost',
        'port': 27017,
        'database': 'brickserver'
    },
    'influx': {
        'server': 'localhost',
        'port': 8086,
        'database': 'brickserver'
    }
}
if os.path.isfile('config.json'):
    config.update(json.loads(open('config.json', 'r').read().strip()))
else:  # pragma: no cover
    open('config.json', 'w').write(json.dumps(config, indent=2, sort_keys=True))

temp_sensor_defaults = {
    '_id': None,
    'desc': None,
    'last_reading': None,
    'prev_reading': None,
    'corr': None
}

latch_defaults = {
    '_id': None,
    'desc': None,
    'last_state': None,
    'last_ts': None,
    'prev_state': None,
    'prev_ts': None,
    'triggers': list(),
    'states_desc': list(['low', 'high', 'falling-edge', 'rising-edge', 'rising-bump', 'falling-bump'])
}


def send_telegram(message):
    if 'environment' in cherrypy.config and cherrypy.config['environment'] == 'test_suite':
        with open('/tmp/telegram_messages', 'a') as f:
            f.write(message + '\n')
    else:  # pragma: no cover
        print('Sending Telegram: ' + message)
        if config['telegram_cmd']:
            subprocess.check_output(config['telegram_cmd'].replace('%m', message), shell=True)


def get_deviceid(ip):  # pragma: no cover
    if ip == '127.0.0.1':
        return 'localhost'
    r = subprocess.check_output('cat /proc/net/arp | grep ' + str(ip), shell=True).decode('utf-8')
    return r.strip().split()[3].replace(':', '')


def version_less_than(a, b):
    """
    executes a < b
    up to three dots are valid: major.minor.patch.fix
    version_less_than('1.0', '1.0.1') => True
    version_less_than('1.0', '1.0') => False
    version_less_than('1.0.1', '1.0') => False
    """
    a = a.split('.')
    while len(a) < 4:
        a.append('0')
    b = b.split('.')
    while len(b) < 4:
        b.append('0')
    for i in range(4):
        if int(a[i]) > int(b[i]):
            return False
        if int(a[i]) < int(b[i]):
            return True
    return False


def version_greater_or_equal_than(a, b):
    """
    executes a >= b
    up to three dots are valid: major.minor.patch.fix
    version_greater_or_equal_than('1.0', '1.0.1') => False
    version_greater_or_equal_than('1.0', '1.0') => True
    version_greater_or_equal_than('1.0.1', '1.0') => True
    """
    a = a.split('.')
    while len(a) < 4:
        a.append('0')
    b = b.split('.')
    while len(b) < 4:
        b.append('0')
    for i in range(4):
        if int(a[i]) < int(b[i]):
            return False
    return True


prediction_ref = list()
for line in open('bat_prediction_reference.dat', 'r').read().strip().split('\n'):
    ts, v = line.split(';')
    prediction_ref.append((int(ts), float(v)))


def calculate_bat_prediction(brick=None, init_ts=None, init_voltage=None, last_ts=None, last_voltage=None):
    if brick is not None:
        init_ts = brick['bat_init_ts']
        init_voltage = brick['bat_init_voltage']
        last_ts = brick['bat_last_ts']
        last_voltage = brick['bat_last_reading']
    if init_ts is None or init_voltage is None:
        return None
    if last_voltage >= init_voltage or init_ts == last_ts:
        return None
    ref_init_ts = None
    ref_last_ts = None
    for ref_ts, ref_voltage in prediction_ref:
        if ref_init_ts is None and init_voltage >= ref_voltage:
            ref_init_ts = ref_ts
            continue
        if last_voltage > ref_voltage:
            ref_last_ts = ref_ts
            break
    if ref_last_ts is None:
        ref_last_ts = prediction_ref[-1][0]

    factor = (datetime.fromtimestamp(prediction_ref[-1][0]) - datetime.fromtimestamp(ref_last_ts)).total_seconds() / (datetime.fromtimestamp(ref_last_ts) - datetime.fromtimestamp(ref_init_ts)).total_seconds()
    prediction = (datetime.fromtimestamp(last_ts) - datetime.fromtimestamp(init_ts)).total_seconds() * factor
    return (prediction / 60 / 60 / 24)
