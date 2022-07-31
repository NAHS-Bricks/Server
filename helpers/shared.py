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
    },
    'mqtt': {
        'server': 'localhost',
        'port': 1883,
        'clientid': 'brickserver'
    },
    's3': {
        'server': 'localhost',
        'port': 9000,
        'bucket': 'brickserver',
        'access_key': 'brickserver',
        'access_secret': 'password'
    },
    'ds': {
        'server': 's3.eu-central-003.backblazeb2.com',
        'port': 443,
        'bucket': 'BrickServer-Downstream',
        'access_key': '00364962f9c8e700000000005',
        'access_secret': 'K003E2hhtN3dEH85EWxWfvCNL8wVmbI'
    },
    'allow': {
        'ds': False
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
    'corr': None,
    'disables': list()
}

humid_defaults = {
    '_id': None,
    'desc': None,
    'last_reading': None,
    'last_ts': None,
    'prev_reading': None,
    'prev_ts': None,
    'corr': None,
    'disables': list()
}

latch_defaults = {
    '_id': None,
    'desc': None,
    'last_state': None,
    'last_ts': None,
    'prev_state': None,
    'prev_ts': None,
    'triggers': list(),
    'states_desc': list(['low', 'high', 'falling-edge', 'rising-edge', 'rising-bump', 'falling-bump']),
    'disables': list()
}

signal_defaults = {
    '_id': None,
    'desc': None,
    'state': 0,
    'state_set_ts': None,  # time on which the state was set via API
    'state_transmitted_ts': None,  # time on which the state was transmitted to brick (or None if set but not yet transmitted)
    'states_desc': list(['off', 'on']),
    'disables': list(['metric'])
}

fanctl_defaults = {
    '_id': None,
    'desc': None,
    'mode': None,  # None: UNKNOWN, -1: NOT_SET, 0: PWM, 1: FLX, 2: BARE
    'mode_transmitted_ts': None,  # time on which mode was transmitted to or received from brick (or None if changed but not yet transmitted)
    'dutyCycle': None,
    'dutyCycle_transmitted_ts': None,  # time on which dutyCycle was transmitted to brick (or None if changed but not yet transmitted)
    'state': None,  # state as received from brick
    'state_should': None,  # state as it should be send to brick (or None if state is not meant to be changed)
    'last_rps': None,
    'last_ts': None,
    'disables': list(['metric'])
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

    r = ((((last_ts - init_ts) / (last_voltage - init_voltage)) * (3.4 - init_voltage)) - (last_ts - init_ts)) / 86400
    if last_voltage > 4.08:
        r *= (last_voltage - 4.08) * 10 + 1
    return r
