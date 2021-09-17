import io
import os
import unittest
import json
import cherrypy
from cherrypy.lib import httputil
from brickserver import Brickserver
from pymongo import MongoClient
from parameterized import parameterized_class
from connector.mqtt import start_async_worker as mqtt_start_worker, _publish_async as mqtt_publish_async
from connector.influxdb import start_async_worker as influxdb_start_worker
import copy
from threading import Thread
import time
import paho.mqtt.client as mqtt

local = httputil.Host('127.0.0.1', 50000, '')
remote = httputil.Host('127.0.0.1', 50001, '')

mqtt_receiver = None
mqtt_receiver_str = ""


def getVersionParameter(myFeature, forbiddenCombinations=None, specificVersion=None, minVersion=dict(), maxVersion=dict()):
    testscale = os.environ.get('TESTSCALE')
    if testscale is None:
        testscale = 'normal'

    f = {
        'all': ['all', 1.02],
        'os': ['os', 1],
        'sleep': ['sleep', 1.01],
        'bat': ['bat', 1],
        'temp': ['temp', 1],
        'humid': ['humid', 1],
        'latch': ['latch', 1],
        'signal': ['signal', 1]
    }

    if isinstance(specificVersion, list):
        for feature, version in specificVersion:
            f[feature] = [feature, version]

    r = list()
    if not isinstance(myFeature, list):
        myFeature = list([myFeature])
    v = list([f.pop('all'), f.pop('os')])
    v += [f[my] for my in myFeature if my in f]
    if testscale == 'long':
        def combinations(base, comming):
            result = list()
            for multi in range(0, int((base[1] - 1) / 0.01) + 1):
                if len(comming) > 1:
                    for later in combinations(comming[0], comming[1:]):
                        this = [[base[0], base[1] - multi * 0.01]]
                        this += later
                        if (this[0][0] not in minVersion or this[0][1] >= minVersion[this[0][0]]) and (this[0][0] not in maxVersion or this[0][1] <= maxVersion[this[0][0]]):
                            result.append(this)
                elif len(comming) == 1:
                    for later in combinations(comming[0], comming[1:]):
                        this = [[base[0], base[1] - multi * 0.01]]
                        this += later
                        if (this[0][0] not in minVersion or this[0][1] >= minVersion[this[0][0]]) and (this[0][0] not in maxVersion or this[0][1] <= maxVersion[this[0][0]]):
                            result.append(this)
                else:
                    this = [[base[0], base[1] - multi * 0.01]]
                    if (this[0][0] not in minVersion or this[0][1] >= minVersion[this[0][0]]) and (this[0][0] not in maxVersion or this[0][1] <= maxVersion[this[0][0]]):
                        result.append(this)
            return result
        for c in combinations(v[0], v[1:]):
            r.append({'name': str(c), 'v': c})
    else:
        r.append({'name': str(v), 'v': v})

    if forbiddenCombinations is None:
        forbiddenCombinations = list()
    if isinstance(forbiddenCombinations, str):
        if forbiddenCombinations == '*':
            forbiddenCombinations = list(f.keys())
        else:
            forbiddenCombinations = list([forbiddenCombinations])

    if not testscale == 'short':
        for k in [k for k in f if k not in myFeature and k not in forbiddenCombinations]:
            v2 = copy.deepcopy(v)
            v2.append(f[k])
            r.append({'name': f'with_{k}_v{v2[-1][1]}', 'v': v2})
            if testscale == 'long' and v2[-1][1] > 1:
                for multi in range(1, int((v2[-1][1] - 1) / 0.01) + 1):
                    v3 = copy.deepcopy(v2)
                    v3[-1][1] = v3[-1][1] - multi * 0.01
                    r.append({'name': f'with_{k}_v{v3[-1][1]}', 'v': v3})
    return r


def mqtt_start_receiver():
    global mqtt_receiver
    global mqtt_receiver_str

    def _mqtt_receiver_thread():
        def on_message(client, userdata, message):
            global mqtt_receiver_str
            mqtt_receiver_str += f'{message.topic} {message.payload.decode("utf-8")}\n'
        if os.path.isfile('config.json'):
            with open('config.json', 'r') as f:
                config = json.loads(f.read().strip())
            client = mqtt.Client("brickserver_test")
            client.on_message = on_message
            client.connect(config['mqtt']['server'])
            client.loop_start()
            client.subscribe("brick/#")
            while True:
                time.sleep(10)

    if mqtt_receiver is None:
        mqtt_receiver = Thread(target=_mqtt_receiver_thread, daemon=True)
        mqtt_receiver.start()


def setUpModule():
    influxdb_start_worker()
    mqtt_start_worker()
    mqtt_start_receiver()
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
    def webapp_request(self, path='/', clear_state=False, ignore_brick_id=False, mqtt_test=False, **kwargs):
        global mqtt_receiver_str
        mqtt_receiver_str = ""
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

        if mqtt_test:
            # sending a mqtt message, that test is done
            mqtt_publish_async('brick/test_done', 1)
            # waiting for the done message to be received
            while 'test_done' not in mqtt_receiver_str:
                time.sleep(0.01)
            # copy the recieved mqtt messages to the response
            response.mqtt = mqtt_receiver_str
        else:
            response.mqtt = ''

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
            response.humid_sensors = {}
            for sensor in mongoDB.humid_sensors.find({}):
                response.humid_sensors[sensor['_id']] = sensor
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
