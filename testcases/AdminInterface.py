from ._wrapper import *

admininterface_versions = [['os', 1.0], ['all', 1.0]]


class TestAdminInterface(BaseCherryPyTestCase):
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
        self.assertEqual(response.json, {'s': 0})
        response = self.webapp_request(path="/admin", command="get_bricks")
        self.assertIn('bricks', response.json)
        self.assertNotIn('unknown', response.json['bricks'])
        response = self.webapp_request(path="/admin", command="get_brick", brick="unknown")
        self.assertNotIn('brick', response.json)
        response = self.webapp_request(path="/admin", command="set", brick="unknown", key='somekey', value='somevalue')
        self.assertEqual(response.json, {'s': 3})

    def test_forgotten_params(self):
        response = self.webapp_request(clear_state=True, v=admininterface_versions, f=[])
        response = self.webapp_request()
        self.assertEqual(response.json, {'s': 0})
        response = self.webapp_request(path="/admin")
        self.assertEqual(response.json, {'s': 1})
        response = self.webapp_request(path="/admin", command='set')
        self.assertEqual(response.json, {'s': 2})
        response = self.webapp_request(path="/admin", command='set', key='somekey')
        self.assertEqual(response.json, {'s': 2})
        response = self.webapp_request(path="/admin", command='set', value='somevalue')
        self.assertEqual(response.json, {'s': 2})

    def test_brick_desc(self):
        response = self.webapp_request(clear_state=True, v=admininterface_versions, f=[])
        response = self.webapp_request()
        self.assertEqual(response.json, {'s': 0})
        response = self.webapp_request(path="/admin", command='set', brick="localhost", key="desc", value='a test host')
        self.assertEqual(response.json, {'s': 0})
        self.assertEqual(response.state['desc'], 'a test host')
