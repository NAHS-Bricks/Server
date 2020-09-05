import cherrypy
import json
import subprocess
import time


storagedir = '/media/ramdisk/'


def get_deviceid(ip):
    r = subprocess.check_output('cat /proc/net/arp | grep ' + str(ip), shell=True)
    return r.strip().split()[3].replace(':', '')


class HelloWorld(object):
    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index(self):
        if 'json' in dir(cherrypy.request):
            data = cherrypy.request.json
            if 'temp' in data:
                ip = cherrypy.request.remote.ip
                open(storagedir + get_deviceid(ip) + '.csv', 'a').write(str(int(time.time())) + ';' + str(data['temp']) + '\n')
            print json.dumps(data)
        return {'state': 'ok'}


if __name__ == '__main__':
    cherrypy.config.update({'server.socket_host': '0.0.0.0',
                        'server.socket_port': 8081,
                       })
    cherrypy.quickstart(HelloWorld())
