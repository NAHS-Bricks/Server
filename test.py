import requests
import json
import time
import unittest


config = json.loads(open('config.json', 'r').read().strip())
storagedir = config['storagedir'] if config['storagedir'].endswith('/') else config['storagedir'] + '/'
statefile = storagedir + config['statefile']
url = 'http://localhost:' + str(config['server_port'])

session = requests.Session()
session.headers = {
    'content-type': "application/json"
}


def state():
    with open(statefile, 'r') as f:
        r = json.loads(f.read().strip())['localhost']
    return r


def send(payload):
    global session
    payload = json.dumps(payload)
    session.post(url, payload)


class TestBrickServer(unittest.TestCase):

    def test_setup(self):
        send({'f': ['temp', 'bat'], 'v': 1.0})
        s = state()
        self.assertEqual(s['version'], 1.0)
        self.assertEqual(s['features'], ['temp', 'bat'])


if __name__ == '__main__':
    unittest.main()
