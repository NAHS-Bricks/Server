from ._wrapper import *


@parameterized_class(getVersionParameter('temp'))
class TestFeatureTemp(BaseCherryPyTestCase):
    def test_temperatures_are_stored(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        self.assertIn('temp_sensors', response.state)
        self.assertEqual(len(response.state['temp_sensors']), 0)

        response = self.webapp_request(t=[['s1', 24]])
        self.assertEqual(len(response.state['temp_sensors']), 1)
        self.assertIn('s1', response.state['temp_sensors'])
        self.assertIn('s1', response.temp_sensors)
        self.assertEqual(response.temp_sensors['s1']['last_reading'], 24)

        response = self.webapp_request(t=[['s1', 25], ['s2', 23]])
        self.assertEqual(len(response.state['temp_sensors']), 2)
        self.assertIn('s1', response.state['temp_sensors'])
        self.assertIn('s2', response.state['temp_sensors'])
        self.assertIn('s1', response.temp_sensors)
        self.assertIn('s2', response.temp_sensors)
        self.assertEqual(response.temp_sensors['s1']['last_reading'], 25)
        self.assertEqual(response.temp_sensors['s1']['prev_reading'], 24)
        self.assertEqual(response.temp_sensors['s2']['last_reading'], 23)

        response = self.webapp_request(t=[['s1', 25], ['s2', 23], ['s3', 22], ['s4', 21], ['s5', 20], ['s6', 21], ['s7', 22], ['s8', 23], ['s9', 24]])
        self.assertEqual(len(response.state['temp_sensors']), 9)  # there shouldn't be a limitation on how many sensors are possible by BrickServer

    def test_precision_is_requested_and_stored(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        self.assertIsNone(response.state['temp_precision'])
        self.assertIn('r', response.json)
        self.assertIn(6, response.json['r'])

        response = self.webapp_request()
        self.assertIsNone(response.state['temp_precision'])
        self.assertIn('r', response.json)
        self.assertIn(6, response.json['r'])

        response = self.webapp_request(p=11)
        self.assertEqual(response.state['temp_precision'], 11)
        if 'r' in response.json:
            self.assertNotIn(6, response.json['r'])

        response = self.webapp_request(p=9)
        self.assertEqual(response.state['temp_precision'], 9)
        if 'r' in response.json:
            self.assertNotIn(6, response.json['r'])

    def test_correction_is_requested_and_stored(self):
        response = self.webapp_request(clear_state=True, y=['i'], v=self.v)
        self.assertIn('temp_sensors', response.state)
        self.assertEqual(len(response.state['temp_sensors']), 0)
        self.assertIn('r', response.json)
        self.assertIn(4, response.json['r'])

        response = self.webapp_request()
        if 'r' in response.json:
            self.assertNotIn(4, response.json['r'])  # it's just requested after init

        response = self.webapp_request(c=[['s1', 1]])
        if 'r' in response.json:
            self.assertNotIn(4, response.json['r'])
        self.assertEqual(len(response.state['temp_sensors']), 1)
        self.assertIn('s1', response.state['temp_sensors'])
        self.assertIn('s1', response.temp_sensors)
        self.assertEqual(response.temp_sensors['s1']['corr'], 1)

        response = self.webapp_request(c=[['s1', 0.5], ['s2', -1]])
        if 'r' in response.json:
            self.assertNotIn(4, response.json['r'])
        self.assertEqual(len(response.state['temp_sensors']), 2)
        self.assertIn('s1', response.state['temp_sensors'])
        self.assertIn('s2', response.state['temp_sensors'])
        self.assertIn('s1', response.temp_sensors)
        self.assertIn('s2', response.temp_sensors)
        self.assertEqual(response.temp_sensors['s1']['corr'], 0.5)
        self.assertEqual(response.temp_sensors['s2']['corr'], -1)

        response = self.webapp_request(t=[['s1', 25], ['s2', 25], ['s3', 25]])  # now adding a new sensor by transmitting it's temp, the correction should be requested as it's unknown on this one
        self.assertIn('r', response.json)
        self.assertIn(4, response.json['r'])

        response = self.webapp_request(c=[['s3', 2]])
        if 'r' in response.json:
            self.assertNotIn(4, response.json['r'])
        self.assertEqual(len(response.state['temp_sensors']), 3)
        self.assertIn('s1', response.state['temp_sensors'])
        self.assertIn('s2', response.state['temp_sensors'])
        self.assertIn('s3', response.state['temp_sensors'])
        self.assertIn('s1', response.temp_sensors)
        self.assertIn('s2', response.temp_sensors)
        self.assertIn('s3', response.temp_sensors)
        self.assertEqual(response.temp_sensors['s1']['corr'], 0.5)
        self.assertEqual(response.temp_sensors['s2']['corr'], -1)
        self.assertEqual(response.temp_sensors['s3']['corr'], 2)

    def test_new_precision_is_submitted(self):  # via admin override
        response = self.webapp_request(clear_state=True, v=self.v)
        self.assertNotIn('p', response.json)

        self.webapp_request(path='/admin', command='set', brick='localhost', key='temp_precision', value=10)
        response = self.webapp_request()
        self.assertIn('p', response.json)
        self.assertEqual(response.json['p'], 10)

        response = self.webapp_request()
        self.assertNotIn('p', response.json)

    def test_max_temp_diff(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        self.assertIn('temp_max_diff', response.state)
        self.assertEqual(response.state['temp_max_diff'], 0)

        response = self.webapp_request(t=[['s1', 25], ['s2', 23]])
        self.assertEqual(response.state['temp_max_diff'], 0)

        response = self.webapp_request(t=[['s1', 26], ['s2', 23]])
        self.assertEqual(response.state['temp_max_diff'], 1)

        response = self.webapp_request(t=[['s1', 26], ['s2', 23.5]])
        self.assertEqual(response.state['temp_max_diff'], 0.5)

        response = self.webapp_request(t=[['s1', 26.75], ['s2', 24]])
        self.assertEqual(response.state['temp_max_diff'], 0.75)

        response = self.webapp_request(t=[['s1', 26], ['s2', 24]])
        self.assertEqual(response.state['temp_max_diff'], 0.75)

        response = self.webapp_request(t=[['s1', 26], ['s2', 23]])
        self.assertEqual(response.state['temp_max_diff'], 1)

        response = self.webapp_request(t=[['s1', 26], ['s2', 23]])
        self.assertEqual(response.state['temp_max_diff'], 0)
