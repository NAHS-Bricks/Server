import cherrypy
import json
import subprocess
import time
import os


config = {'storagedir': '/tmp', 'statefile': 'state.json'}
if os.path.isfile('config.json'):
    config.update(json.loads(open('config.json', 'r').read().strip()))
else:
    open('config.json', 'w').write(json.dumps(config, indent=2, sort_keys=True))
storagedir = config['storagedir'] if config['storagedir'].endswith('/') else config['storagedir'] + '/'
statefile = storagedir + config['statefile']

brick_state_defaults = {
    'all': {
        'id': None
        'version': None,
        'features': [],
        'desc': '',
        'last_ts': None
    },
    'temp': {
        'last_temps': {},
        'presicion': 11,
        'delay': 60
    }
}
bricks = {}
if os.path.isfile(statefile):
    bricks = json.loads(open(statefile, 'r').read().strip())


def __key_v(brick, value):
    brick['version'] = value


def __key_f(brick, value):
    for feature in [f for f in value if f not in brick['features']]:
        brick.update(brick_state_defaults[feature])
        brick['features'].append(feature)


def __key_t(brick, temps):
    if 'temp' not in brick['features']:
        return
    for sensor, temp in temps:
        storagefile = storagedir + brick['id'] + '_' + sensor + '.csv'
        entryline = brick['last_ts'] + ';' + str(temp) + '\n'
        open(storagefile, 'a').write(entryline)
        brick['last_temps'][sensor] = temp

key_function = {
    'v': __key_v,
    'f': __key_f,
    't': __key_t
}

def get_deviceid(ip):
    r = subprocess.check_output('cat /proc/net/arp | grep ' + str(ip), shell=True)
    return r.strip().split()[3].replace(':', '')


"""
Input json keys:
t = list of sensors with temps, where sensor and temp are lists themself (eg: [['s1', t1], ['s2', t2]] )
v = bricks software version
f = list of bricks features as in brick_state_defaults

Output json keys:
"""
class Tempserver(object):
    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index(self):
        if 'json' in dir(cherrypy.request):
            data = cherrypy.request.json
            brick_ip = cherrypy.request.remote.ip
            brick_id = get_deviceid(device_ip)
            if brick_id not in bricks:
                bricks[brick_id] = {}
                bricks[brick_id].update(brick_state_defaults['all'])
                bricks[brick_id]['id'] = brick_id
            bricks[brick_id]['last_ts'] = str(int(time.time()))

            [key_function[k](bricks[brick_id], data[k]) for k in data if k in key_function]
            open(statefile, 'w').write(json.dumps(bricks, indent=2))
        return {'state': 'ok'}


if __name__ == '__main__':
    cherrypy.config.update({'server.socket_host': '0.0.0.0',
                        'server.socket_port': 8081,
                       })
    cherrypy.quickstart(Tempserver())
