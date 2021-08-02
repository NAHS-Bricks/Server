import io
import os
import unittest
import json
import cherrypy
from cherrypy.lib import httputil
from brickserver import Brickserver
from pymongo import MongoClient
from parameterized import parameterized_class
import copy
from event.worker import start_thread as event_worker

local = httputil.Host('127.0.0.1', 50000, '')
remote = httputil.Host('127.0.0.1', 50001, '')


def getVersionParameter(myFeature, forbiddenCombinations=None):
    f = {
        'sleep': ['sleep', 1],
        'bat': ['bat', 1],
        'temp': ['temp', 1],
        'latch': ['latch', 1],
        'signal': ['signal', 1]
    }
    if forbiddenCombinations is None:
        forbiddenCombinations = list()
    r = list()
    if not isinstance(myFeature, list):
        myFeature = list([myFeature])
    v = list([['all', 1], ['os', 1]])
    v += [f[my] for my in myFeature if my in f]
    r.append({'name': 'standalone', 'v': v})
    for k in [k for k in f if k not in myFeature and k not in forbiddenCombinations]:
        v2 = copy.deepcopy(v)
        v2.append(f[k])
        r.append({'name': 'with_' + k, 'v': v2})
    return r


def setUpModule():
    cherrypy.config.update({'environment': 'test_suite'})

    # start the event_worker in background
    event_worker()

    # prevent the HTTP server from ever starting
    cherrypy.server.unsubscribe()

    cherrypy.tree.mount(Brickserver(), '/')
    cherrypy.engine.start()


setup_module = setUpModule


def tearDownModule():
    cherrypy.engine.exit()


teardown_module = tearDownModule


class BaseCherryPyTestCase(unittest.TestCase):
    def webapp_request(self, path='/', clear_state=False, ignore_brick_id=False, **kwargs):
        if clear_state and os.path.isfile('config.json'):
            with open('config.json', 'r') as f:
                config = json.loads(f.read().strip())
            mongoClient = MongoClient(host=config['mongo']['server'], port=int(config['mongo']['port']))
            mongoDB = mongoClient.get_database(config['mongo']['database'])
            for c in mongoDB.list_collections():
                mongoDB.get_collection(c['name']).drop()
        cherrypy.config.update({'ignore_brick_identification': ignore_brick_id})

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
            mongoClient = MongoClient(host=config['mongo']['server'], port=int(config['mongo']['port']))
            mongoDB = mongoClient.get_database(config['mongo']['database'])
            response.state = mongoDB.bricks.find_one({'_id': 'localhost'})
            if response.state is None:
                response.state = {}
            response.temp_sensors = {}
            for sensor in mongoDB.temp_sensors.find({}):
                response.temp_sensors[sensor['_id']] = sensor
            response.latches = {}
            for latch in mongoDB.latches.find({}):
                response.latches[latch['_id']] = latch
            response.signals = {}
            for signal in mongoDB.signals.find({}):
                response.signals[signal['_id']] = signal
            response.cron_data = mongoDB.util.find_one({'_id': 'cron_data'})
            if response.cron_data is None:
                response.cron_data = {}
            if os.path.isfile('/tmp/telegram_messages'):
                with open('/tmp/telegram_messages', 'r') as f:
                    response.telegram = f.read().strip()
            else:
                response.telegram = ""
        else:
            response.state = {}
            response.temp_sensors = {}
            response.cron_data = {}
            response.telegram = ""

        return response
