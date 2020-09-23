import requests
import json
import time
import unittest
import subprocess
import os
import warnings
import signal


config = json.loads(open('config.json', 'r').read().strip())
storagedir = config['storagedir'] if config['storagedir'].endswith('/') else config['storagedir'] + '/'
statefile = storagedir + config['statefile']
url = 'http://localhost:' + str(config['server_port'])

session = requests.Session()
session.headers = {
    'content-type': "application/json"
}
brickserver_process = None


def state():
    with open(statefile, 'r') as f:
        r = json.loads(f.read().strip())['localhost']
    return r


def send(payload):
    global session
    payload = json.dumps(payload)
    return session.post(url, payload).json()


def server_start():
    global brickserver_process
    warnings.filterwarnings(action="ignore", message="unclosed", category=ResourceWarning)
    brickserver_process = subprocess.Popen(
        ["./venv/bin/python", "brickserver.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(1)


def server_stop():
    global brickserver_process
    brickserver_process.stdin.close()
    brickserver_process.send_signal(signal.SIGINT)
    brickserver_process.terminate()
    brickserver_process.wait(timeout=0.2)


def server_cleanrestart():
    print('Restarting Server...')
    server_stop()
    time.sleep(1)
    if os.path.isfile(statefile):
        os.remove(statefile)
    server_start()


class TestBrickServer(unittest.TestCase):
    def setUp(self):
        warnings.filterwarnings(action="ignore", message="unclosed", category=ResourceWarning)
        if os.path.isfile(statefile):
            os.remove(statefile)
        self.brickserver = subprocess.Popen(["./venv/bin/python", "brickserver.py"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(1)

    def tearDown(self):
        self.brickserver.stdin.close()
        self.brickserver.terminate()
        self.brickserver.wait(timeout=1)

    def test_setup(self):
        send({'f': ['temp', 'bat'], 'v': 1.0})
        s = state()
        self.assertEqual(s['version'], 1.0)
        self.assertEqual(s['features'], ['temp', 'bat'])

    def test_delay_increase(self):
        send({'f': ['temp', 'bat'], 'v': 1.0, 't': [['sensor1', 25]]})
        send({'t': [['sensor1', 24]]})
        s = state()
        self.assertEqual(s['delay'], 60)
        self.assertEqual(s['delay_increase_wait'], 3)
        r = send({'t': [['sensor1', 24]]})
        self.assertNotIn('d', r)
        s = state()
        self.assertEqual(s['delay'], 60)
        self.assertEqual(s['delay_increase_wait'], 2)
        r = send({'t': [['sensor1', 24]]})
        self.assertNotIn('d', r)
        s = state()
        self.assertEqual(s['delay'], 60)
        self.assertEqual(s['delay_increase_wait'], 1)
        r = send({'t': [['sensor1', 24]]})
        self.assertIn('d', r)
        self.assertEqual(r['d'], 120)
        s = state()
        self.assertEqual(s['delay'], 120)
        self.assertEqual(s['delay_increase_wait'], 3)
        r = send({'t': [['sensor1', 24.25]]})
        self.assertNotIn('d', r)
        s = state()
        self.assertEqual(s['delay'], 120)
        self.assertEqual(s['delay_increase_wait'], 2)
        r = send({'t': [['sensor1', 24.51]]})
        self.assertIn('d', r)
        self.assertEqual(r['d'], 60)
        s = state()
        self.assertEqual(s['delay'], 60)
        self.assertEqual(s['delay_increase_wait'], 3)
        r = send({'t': [['sensor1', 25]]})
        self.assertNotIn('d', r)
        s = state()
        self.assertEqual(s['delay'], 60)
        self.assertEqual(s['delay_increase_wait'], 3)

    def test_delay_increase_to_max(self):
        send({'f': ['temp', 'bat'], 'v': 1.0, 't': [['sensor1', 25]]})
        send({'t': [['sensor1', 24]]})
        s = state()
        self.assertEqual(s['delay'], 60)
        self.assertEqual(s['delay_increase_wait'], 3)
        send({'t': [['sensor1', 24.1]]})
        send({'t': [['sensor1', 24.2]]})
        send({'t': [['sensor1', 24.3]]})
        s = state()
        self.assertEqual(s['delay'], 120)
        self.assertEqual(s['delay_increase_wait'], 3)
        send({'t': [['sensor1', 24.4]]})
        send({'t': [['sensor1', 24.5]]})
        send({'t': [['sensor1', 24.6]]})
        s = state()
        self.assertEqual(s['delay'], 180)
        self.assertEqual(s['delay_increase_wait'], 3)
        send({'t': [['sensor1', 24.7]]})
        send({'t': [['sensor1', 24.8]]})
        send({'t': [['sensor1', 24.9]]})
        s = state()
        self.assertEqual(s['delay'], 240)
        self.assertEqual(s['delay_increase_wait'], 3)
        send({'t': [['sensor1', 25]]})
        send({'t': [['sensor1', 25.1]]})
        send({'t': [['sensor1', 25.2]]})
        s = state()
        self.assertEqual(s['delay'], 300)
        self.assertEqual(s['delay_increase_wait'], 3)
        send({'t': [['sensor1', 25.3]]})
        send({'t': [['sensor1', 25.4]]})
        send({'t': [['sensor1', 25.5]]})
        s = state()
        self.assertEqual(s['delay'], 300)
        self.assertEqual(s['delay_increase_wait'], 0)

    def test_bat_charging(self):
        r = send({'f': ['temp', 'bat'], 'v': 1.0, 'y': []})
        self.assertIn('r', r)
        self.assertIn('b', r['r'])
        s = state()
        self.assertIsNone(s['last_bat_ts'])
        r = send({'b': 3.6})
        self.assertNotIn('r', r)
        s = state()
        self.assertFalse(s['bat_charging'])
        self.assertFalse(s['bat_charging_standby'])
        send({'y': ['c']})
        s = state()
        self.assertTrue(s['bat_charging'])
        self.assertFalse(s['bat_charging_standby'])
        send({'y': ['s']})
        s = state()
        self.assertFalse(s['bat_charging'])
        self.assertTrue(s['bat_charging_standby'])
        send({'y': []})
        s = state()
        self.assertFalse(s['bat_charging'])
        self.assertFalse(s['bat_charging_standby'])


if __name__ == '__main__':
    warnings.filterwarnings(action="ignore", message="unclosed", category=ResourceWarning)
    #print('Starting Server...')
    #server_start()
    unittest.main()
    #server_stop()
