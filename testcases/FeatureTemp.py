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

    def test_valid_values_for_temp_precision(self):  # via admin override
        response = self.webapp_request(clear_state=True, v=self.v)
        response = self.webapp_request(path='/admin', command='set', brick='localhost', key='temp_precision', value=8)
        self.assertEqual(response.json['s'], 7)
        response = self.webapp_request(path='/admin', command='set', brick='localhost', key='temp_precision', value=9)
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', brick='localhost', key='temp_precision', value=10)
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', brick='localhost', key='temp_precision', value=11)
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', brick='localhost', key='temp_precision', value=12)
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', brick='localhost', key='temp_precision', value=13)
        self.assertEqual(response.json['s'], 7)

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

    def test_get_temp_sensor(self):  # via AdminInterface
        response = self.webapp_request(clear_state=True, v=self.v, t=[['s1', 24], ['s2', 25]])

        response = self.webapp_request(path='/admin', command='get_temp_sensor', temp_sensor='s1')
        self.assertIn('temp_sensor', response.json)
        self.assertIn('_id', response.json['temp_sensor'])
        self.assertEqual(response.json['temp_sensor']['_id'], 's1')
        self.assertIn('last_reading', response.json['temp_sensor'])
        self.assertEqual(response.json['temp_sensor']['last_reading'], 24)

        response = self.webapp_request(path='/admin', command='get_temp_sensor', temp_sensor='s2')
        self.assertIn('temp_sensor', response.json)
        self.assertIn('_id', response.json['temp_sensor'])
        self.assertEqual(response.json['temp_sensor']['_id'], 's2')
        self.assertIn('last_reading', response.json['temp_sensor'])
        self.assertEqual(response.json['temp_sensor']['last_reading'], 25)

    def test_delete_brick_with_sensors(self):
        response = self.webapp_request(clear_state=True, v=self.v, t=[['s1', 24], ['s2', 25]])
        self.assertNotEqual(response.state, {})
        self.assertIn('s1', response.temp_sensors)
        self.assertIn('s2', response.temp_sensors)
        response = self.webapp_request(path="/admin", command='delete_brick', brick='localhost')
        self.assertIn('deleted', response.json)
        self.assertEqual(response.json['deleted']['brick'], 'localhost')
        self.assertIn('s1', response.json['deleted']['temp_sensors'])
        self.assertIn('s2', response.json['deleted']['temp_sensors'])
        self.assertEqual(response.state, {})
        self.assertEqual(response.temp_sensors, {})

    def test_temp_sensor_desc_is_stored(self):
        response = self.webapp_request(clear_state=True, v=self.v, t=[['s1', 24], ['s2', 25]])
        self.assertIsNone(response.temp_sensors['s1']['desc'])
        self.assertIsNone(response.temp_sensors['s2']['desc'])

        response = self.webapp_request(path='/admin', command='set', temp_sensor='s1', key='desc', value='sensor1')
        self.assertEqual(response.json['s'], 0)
        self.assertEqual(response.temp_sensors['s1']['desc'], 'sensor1')
        self.assertIsNone(response.temp_sensors['s2']['desc'])

        response = self.webapp_request(path='/admin', command='set', temp_sensor='s2', key='desc', value='sensor2')
        self.assertEqual(response.json['s'], 0)
        self.assertEqual(response.temp_sensors['s1']['desc'], 'sensor1')
        self.assertEqual(response.temp_sensors['s2']['desc'], 'sensor2')

        response = self.webapp_request(path='/admin', command='set', temp_sensor='s1', key='desc', value='sensorX')
        self.assertEqual(response.json['s'], 0)
        self.assertEqual(response.temp_sensors['s1']['desc'], 'sensorX')
        self.assertEqual(response.temp_sensors['s2']['desc'], 'sensor2')

    def test_valid_values_for_disables(self):
        response = self.webapp_request(clear_state=True, v=self.v, t=[['s1', 24], ['s2', 25]])
        # add disable
        response = self.webapp_request(path='/admin', command='set', temp_sensor='s1', key='add_disable', value='ui')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', temp_sensor='s1', key='add_disable', value='metric')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', temp_sensor='s1', key='add_disable', value='invalid')
        self.assertEqual(response.json['s'], 7)
        # del disable
        response = self.webapp_request(path='/admin', command='set', temp_sensor='s1', key='del_disable', value='ui')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', temp_sensor='s1', key='del_disable', value='metric')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', temp_sensor='s1', key='del_disable', value='invalid')
        self.assertEqual(response.json['s'], 7)

    def test_disables_are_stored(self):
        response = self.webapp_request(clear_state=True, v=self.v, t=[['s1', 24], ['s2', 25]])
        self.assertEqual(len(response.temp_sensors['s1']['disables']), 0)
        response = self.webapp_request(path='/admin', command='set', temp_sensor='s1', key='add_disable', value='ui')
        self.assertEqual(len(response.temp_sensors['s1']['disables']), 1)
        self.assertIn('ui', response.temp_sensors['s1']['disables'])
        response = self.webapp_request(path='/admin', command='set', temp_sensor='s1', key='add_disable', value='ui')  # no change allready in list
        self.assertEqual(len(response.temp_sensors['s1']['disables']), 1)
        self.assertIn('ui', response.temp_sensors['s1']['disables'])
        response = self.webapp_request(path='/admin', command='set', temp_sensor='s1', key='add_disable', value='metric')
        self.assertEqual(len(response.temp_sensors['s1']['disables']), 2)
        self.assertIn('ui', response.temp_sensors['s1']['disables'])
        self.assertIn('metric', response.temp_sensors['s1']['disables'])
        response = self.webapp_request(path='/admin', command='set', temp_sensor='s1', key='del_disable', value='ui')
        self.assertEqual(len(response.temp_sensors['s1']['disables']), 1)
        self.assertIn('metric', response.temp_sensors['s1']['disables'])
        response = self.webapp_request(path='/admin', command='set', temp_sensor='s1', key='del_disable', value='ui')  # no change allready removed
        self.assertEqual(len(response.temp_sensors['s1']['disables']), 1)
        self.assertIn('metric', response.temp_sensors['s1']['disables'])
        response = self.webapp_request(path='/admin', command='set', temp_sensor='s1', key='del_disable', value='metric')
        self.assertEqual(len(response.temp_sensors['s1']['disables']), 0)

    def test_temp_sensor_count_is_returned(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        response = self.webapp_request(path='/admin', command='get_count', item='temp_sensors')
        self.assertIn('count', response.json)
        self.assertEqual(response.json['count'], 0)
        response = self.webapp_request(t=[['s1', 24], ['s2', 25]])
        response = self.webapp_request(path='/admin', command='get_count', item='temp_sensors')
        self.assertIn('count', response.json)
        self.assertEqual(response.json['count'], 2)
        response = self.webapp_request(t=[['s1', 24], ['s2', 25], ['s3', 26]])
        response = self.webapp_request(path='/admin', command='get_count', item='temp_sensors')
        self.assertIn('count', response.json)
        self.assertEqual(response.json['count'], 3)

    def test_mqtt_messages_are_send(self):
        response = self.webapp_request(clear_state=True, mqtt_test=True, v=self.v, t=[['s1', 24], ['s2', 25]])
        self.assertIn('brick/localhost/temp/s1 24', response.mqtt)
        self.assertIn('brick/localhost/temp/s2 25', response.mqtt)
        response = self.webapp_request(mqtt_test=True, t=[['s1', 24], ['s2', 25], ['s3', 24.5]])
        self.assertIn('brick/localhost/temp/s1 24', response.mqtt)
        self.assertIn('brick/localhost/temp/s2 25', response.mqtt)
        self.assertIn('brick/localhost/temp/s3 24.5', response.mqtt)

        # disableing latch 1 to send mqtt messages
        response = self.webapp_request(path='/admin', command='set', temp_sensor='s2', key='add_disable', value='mqtt')
        response = self.webapp_request(mqtt_test=True, t=[['s1', 24], ['s2', 25], ['s3', 24.5]])
        self.assertIn('brick/localhost/temp/s1 24', response.mqtt)
        self.assertNotIn('brick/localhost/temp/s2 25', response.mqtt)
        self.assertIn('brick/localhost/temp/s3 24.5', response.mqtt)

        # enable latch 1 to send mqtt messages
        response = self.webapp_request(path='/admin', command='set', temp_sensor='s2', key='del_disable', value='mqtt')
        response = self.webapp_request(mqtt_test=True, t=[['s1', 24], ['s2', 25], ['s3', 24.5]])
        self.assertIn('brick/localhost/temp/s1 24', response.mqtt)
        self.assertIn('brick/localhost/temp/s2 25', response.mqtt)
        self.assertIn('brick/localhost/temp/s3 24.5', response.mqtt)
