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

brick_state_defaults = {
    'all': {
        'id': None,
        'type': None,
        'version': {'os': 0, 'all': 0},
        'features': [],
        'desc': '',
        'last_ts': None,
        'initalized': False
    },
    'temp': {
        'temp_sensors': [],
        'temp_precision': None,
        'temp_max_diff': 0
    },
    'bat': {
        'bat_last_reading': 0,
        'bat_last_ts': None,
        'bat_charging': False,
        'bat_charging_standby': False,
        'bat_periodic_voltage_request': 10
    },
    'sleep': {
        'sleep_delay': 60,
        'sleep_increase_wait': 3
    },
    'latch': {
        'latch_states': [],
        'latch_triggers': []
    }
}

temp_sensor_defaults = {
    '_id': None,
    'desc': '',
    'last_reading': None,
    'prev_reading': None,
    'corr': None
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
