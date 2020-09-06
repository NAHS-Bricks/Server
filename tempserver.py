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


def get_deviceid(ip):
    r = subprocess.check_output('cat /proc/net/arp | grep ' + str(ip), shell=True)
    return r.strip().split()[3].replace(':', '')


"""
Input json keys:
t = list of sensors with temps, where sensor and temp are lists themself (eg: [['s1', t1], ['s2', t2]] )
"""
class Tempserver(object):
    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index(self):
        if 'json' in dir(cherrypy.request):
            data = cherrypy.request.json
            device_ip = cherrypy.request.remote.ip
            device_id = get_deviceid(device_ip)
            timestamp = str(int(time.time()))
            if 't' in data:
                for sensor, temp in data['temps']:
                    storagefile = storagedir + device_id + '_' + sensor + '.csv'
                    entryline = timestamp + ';' + str(temp) + '\n'
                    open(storagefile, 'a').write(entryline)
            elif 'temp' in data:
                open(storagedir + device_id + '.csv', 'a').write(timestamp + ';' + str(data['temp']) + '\n')
                storagefile = storagedir + device_id + '.csv'
                entryline = timestamp + ';' + str(data['temp']) + '\n'
                open(storagefile, 'a').write(entryline)
        return {'state': 'ok'}


if __name__ == '__main__':
    cherrypy.config.update({'server.socket_host': '0.0.0.0',
                        'server.socket_port': 8081,
                       })
    cherrypy.quickstart(Tempserver())
