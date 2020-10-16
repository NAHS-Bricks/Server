import io
import os
import unittest
import json
import cherrypy
from cherrypy.lib import httputil
from brickserver import Brickserver

local = httputil.Host('127.0.0.1', 50000, '')
remote = httputil.Host('127.0.0.1', 50001, '')


def setUpModule():
    cherrypy.config.update({'environment': 'test_suite'})

    # prevent the HTTP server from ever starting
    cherrypy.server.unsubscribe()

    cherrypy.tree.mount(Brickserver(), '/')
    cherrypy.engine.start()


setup_module = setUpModule


def tearDownModule():
    cherrypy.engine.exit()


teardown_module = tearDownModule


class BaseCherryPyTestCase(unittest.TestCase):
    def webapp_request(self, path='/', clear_state=False, **kwargs):
        if clear_state and os.path.isfile('config.json'):
            with open('config.json', 'r') as f:
                config = json.loads(f.read().strip())
            if os.path.isfile(os.path.join(config['storagedir'], config['statefile'])):
                os.remove(os.path.join(config['storagedir'], config['statefile']))

        headers = [('Host', '127.0.0.1')]

        if kwargs:
            qs = json.dumps(kwargs)
        else:
            qs = "{}"
        headers.append(('content-type', 'application/json'))
        headers.append(('content-length', f'{len(qs)}'))
        fd = io.BytesIO(qs.encode())
        qs = None

        # Get our application and run the request against it
        app = cherrypy.tree.apps['']
        # Let's fake the local and remote addresses
        # Let's also use a non-secure scheme: 'http'
        request, response = app.get_serving(local, remote, 'http', 'HTTP/1.1')
        try:
            response = request.run('POST', path, qs, 'HTTP/1.1', headers, fd)
        finally:
            if fd:
                fd.close()
                fd = None

        if response.output_status.startswith(b'500'):
            print(response.body)
            raise AssertionError('Unexpected error')

        # collapse the response into a bytestring
        response.collapse_body()
        try:
            response.json = json.loads(response.body[0])
        except Exception:
            response.json = {}

        if os.path.isfile('config.json'):
            with open('config.json', 'r') as f:
                config = json.loads(f.read().strip())
            if os.path.isfile(os.path.join(config['storagedir'], config['statefile'])):
                with open(os.path.join(config['storagedir'], config['statefile']), 'r') as f:
                    response.state, response.temp_sensors = json.loads(f.read().strip())
                    response.state = response.state['localhost']
            else:
                response.state = {}
                response.temp_sensors = {}
            if os.path.isfile(os.path.join(config['storagedir'], 'telegram_messages')):
                with open(os.path.join(config['storagedir'], 'telegram_messages'), 'r') as f:
                    response.telegram = f.read().strip()
            else:
                response.telegram = ""
        else:
            response.state = {}
            response.temp_sensors = {}
            response.telegram = ""

        return response
