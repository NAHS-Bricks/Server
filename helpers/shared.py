import os
import json
import subprocess
import cherrypy


config = {
    'storagedir': '/tmp/brickserver',
    'statefile': 'state.json',
    'server_port': 8081,
    'telegram_cmd': None,
    'temp_sensor_dir': 'temp_sensors'
}
if os.path.isfile('config.json'):
    config.update(json.loads(open('config.json', 'r').read().strip()))
else:  # pragma: no cover
    open('config.json', 'w').write(json.dumps(config, indent=2, sort_keys=True))
if not os.path.exists(config['storagedir']):  # pragma: no cover
    os.mkdir(config['storagedir'])
if not os.path.exists(os.path.join(config['storagedir'], config['temp_sensor_dir'])):  # pragma: no cover
    os.mkdir(os.path.join(config['storagedir'], config['temp_sensor_dir']))

bricks = {}
temp_sensors = {}
if os.path.isfile(os.path.join(config['storagedir'], config['statefile'])):  # pragma: no cover
    bricks, temp_sensors = json.loads(open(os.path.join(config['storagedir'], config['statefile']), 'r').read().strip())


def send_telegram(message):
    if 'environment' in cherrypy.config and cherrypy.config['environment'] == 'test_suite':
        with open(os.path.join(config['storagedir'], 'telegram_messages'), 'a') as f:
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
