import os
import json
import subprocess
import cherrypy


config = {'storagedir': '/tmp', 'statefile': 'state.json', 'server_port': 8081, 'telegram_cmd': None}
if os.path.isfile('config.json'):
    config.update(json.loads(open('config.json', 'r').read().strip()))
else:  # pragma: no cover
    open('config.json', 'w').write(json.dumps(config, indent=2, sort_keys=True))
storagedir = config['storagedir'] if config['storagedir'].endswith('/') else config['storagedir'] + '/'
statefile = storagedir + config['statefile']


def send_telegram(message):
    if 'environment' in cherrypy.config and cherrypy.config['environment'] == 'test_suite':
        with open(os.path.join(storagedir, 'telegram_messages'), 'a') as f:
            f.write(message + '\n')
    else:  # pragma: no cover
        print('Sending Telegram: ' + message)
        if config['telegram_cmd']:
            subprocess.check_output(config['telegram_cmd'].replace('%m', message), shell=True)
