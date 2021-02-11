from ._wrapper import *
from helpers.shared import brick_state_defaults

admininterface_versions = [['os', 1.0], ['all', 1.0]]


class TestAdminInterface(BaseCherryPyTestCase):
    def test_invalid_comand(self):
        response = self.webapp_request(path="/admin", command="bullshit")
        self.assertEqual(response.json['s'], 2)

    def test_valid_brick(self):
        response = self.webapp_request(clear_state=True, v=admininterface_versions, f=[])
        response = self.webapp_request()
        self.assertEqual(response.json, {'s': 0})
        response = self.webapp_request(path="/admin", command="get_bricks")
        self.assertIn('bricks', response.json)
        self.assertIn('localhost', response.json['bricks'])
        response = self.webapp_request(path="/admin", command="get_brick", brick="localhost")
        self.assertIn('brick', response.json)
        self.assertIn('_id', response.json['brick'])
        self.assertEqual(response.json['brick']['_id'], 'localhost')

    def test_invalid_brick(self):
        response = self.webapp_request(clear_state=True, v=admininterface_versions, f=[])
        response = self.webapp_request()
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path="/admin", command="get_bricks")
        self.assertIn('bricks', response.json)
        self.assertNotIn('unknown', response.json['bricks'])
        response = self.webapp_request(path="/admin", command="get_brick", brick="unknown")
        self.assertNotIn('brick', response.json)
        response = self.webapp_request(path="/admin", command="set", brick="unknown", key='somekey', value='somevalue')
        self.assertEqual(response.json['s'], 3)

    def test_forgotten_params(self):
        response = self.webapp_request(clear_state=True, v=admininterface_versions, f=[])
        response = self.webapp_request()
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path="/admin")
        self.assertEqual(response.json['s'], 1)
        response = self.webapp_request(path="/admin", command='set')
        self.assertEqual(response.json['s'], 4)
        response = self.webapp_request(path="/admin", command='set', key='somekey')
        self.assertEqual(response.json['s'], 5)
        response = self.webapp_request(path="/admin", command='set', value='somevalue')
        self.assertEqual(response.json['s'], 4)

    def test_brick_desc(self):
        response = self.webapp_request(clear_state=True, v=admininterface_versions, f=[])
        response = self.webapp_request()
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path="/admin", command='set', brick="localhost", key="desc", value='a test host')
        self.assertEqual(response.json['s'], 0)
        self.assertEqual(response.state['desc'], 'a test host')

    def test_temp_sensor_desc_and_get_temp_sensor(self):
        response = self.webapp_request(clear_state=True, v=admininterface_versions, f=['temp'], t=[['s1', 24], ['s2', 25]])
        self.assertEqual(response.json['s'], 0)

        # All sensors do not have a desc
        response = self.webapp_request(path="/admin", command='get_temp_sensor', temp_sensor='s1')
        self.assertEqual(response.json['temp_sensor']['_id'], 's1')
        self.assertEqual(response.json['temp_sensor']['desc'], '')
        response = self.webapp_request(path="/admin", command='get_temp_sensor', temp_sensor='s2')
        self.assertEqual(response.json['temp_sensor']['_id'], 's2')
        self.assertEqual(response.json['temp_sensor']['desc'], '')

        # set desc of s1
        response = self.webapp_request(path="/admin", command='set', temp_sensor='s1', key='desc', value='s1 desc')

        # Only s1 has a desc
        response = self.webapp_request(path="/admin", command='get_temp_sensor', temp_sensor='s1')
        self.assertEqual(response.json['temp_sensor']['_id'], 's1')
        self.assertEqual(response.json['temp_sensor']['desc'], 's1 desc')
        response = self.webapp_request(path="/admin", command='get_temp_sensor', temp_sensor='s2')
        self.assertEqual(response.json['temp_sensor']['_id'], 's2')
        self.assertEqual(response.json['temp_sensor']['desc'], '')

        # fire a tempreading, to also send sensor desc to influx
        response = self.webapp_request(t=[['s1', 24], ['s2', 25]])

        # invalid temp_sensor on set desc
        response = self.webapp_request(path="/admin", command='set', temp_sensor='s3', key='desc', value='s3 desc')
        self.assertEqual(response.json['s'], 8)

        # invalid temp_sensor on get sensor
        response = self.webapp_request(path="/admin", command='get_temp_sensor', temp_sensor='s3')
        self.assertEqual(response.json['s'], 8)

    def test_get_features(self):
        response = self.webapp_request(path="/admin", command='get_features')
        self.assertEqual(response.json['s'], 0)
        self.assertEqual(len(response.json['features']), len(brick_state_defaults.keys()) - 1)
        self.assertIn('temp', response.json['features'])
        self.assertIn('bat', response.json['features'])
        self.assertIn('sleep', response.json['features'])
        self.assertIn('latch', response.json['features'])
