import os
import json
import subprocess
import cherrypy


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
    'desc': '',
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
    'triggers': list()
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
    _version_less_than('1.0', '1.0.1') => True
    _version_less_than('1.0', '1.0') => False
    _version_less_than('1.0.1', '1.0') => False
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
        if i == 3:
            if int(a[i]) == int(b[i]):
                return False
            else:
                return True


def version_greater_or_equal_than(a, b):
    """
    executes a >= b
    up to three dots are valid: major.minor.patch.fix
    _version_greater_or_equal_than('1.0', '1.0.1') => False
    _version_greater_or_equal_than('1.0', '1.0') => True
    _version_greater_or_equal_than('1.0.1', '1.0') => True
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
