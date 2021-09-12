from ._wrapper import *


@parameterized_class(getVersionParameter('humid'))
class TestFeatureHumid(BaseCherryPyTestCase):
    def test_humidities_are_stored(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        self.assertIn('humid_sensors', response.state)
        self.assertEqual(len(response.state['humid_sensors']), 0)

        response = self.webapp_request(h=[['h1', 50]])
        self.assertEqual(len(response.state['humid_sensors']), 1)
        self.assertIn('h1', response.state['humid_sensors'])
        self.assertIn('h1', response.humid_sensors)
        self.assertEqual(response.humid_sensors['h1']['last_reading'], 50)

        response = self.webapp_request(h=[['h1', 55], ['h2', 60]])
        self.assertEqual(len(response.state['humid_sensors']), 2)
        self.assertIn('h1', response.state['humid_sensors'])
        self.assertIn('h2', response.state['humid_sensors'])
        self.assertIn('h1', response.humid_sensors)
        self.assertIn('h2', response.humid_sensors)
        self.assertEqual(response.humid_sensors['h1']['last_reading'], 55)
        self.assertEqual(response.humid_sensors['h1']['prev_reading'], 50)
        self.assertEqual(response.humid_sensors['h2']['last_reading'], 60)

        response = self.webapp_request(h=[['h1', 50], ['h2', 51], ['h3', 52], ['h4', 53], ['h5', 54], ['h6', 55], ['h7', 56], ['h8', 57], ['h9', 58]])
        self.assertEqual(len(response.state['humid_sensors']), 9)  # there shouldn't be a limitation on how many sensors are possible by BrickServer

    def test_correction_is_requested_and_stored(self):
        response = self.webapp_request(clear_state=True, y=['i'], v=self.v)
        self.assertIn('humid_sensors', response.state)
        self.assertEqual(len(response.state['humid_sensors']), 0)
        self.assertIn('r', response.json)
        self.assertIn(9, response.json['r'])

        response = self.webapp_request()
        if 'r' in response.json:
            self.assertNotIn(9, response.json['r'])  # it's just requested after init

        response = self.webapp_request(k=[['h1', 1]])
        if 'r' in response.json:
            self.assertNotIn(9, response.json['r'])
        self.assertEqual(len(response.state['humid_sensors']), 1)
        self.assertIn('h1', response.state['humid_sensors'])
        self.assertIn('h1', response.humid_sensors)
        self.assertEqual(response.humid_sensors['h1']['corr'], 1)

        response = self.webapp_request(k=[['h1', 0.5], ['h2', -1]])
        if 'r' in response.json:
            self.assertNotIn(9, response.json['r'])
        self.assertEqual(len(response.state['humid_sensors']), 2)
        self.assertIn('h1', response.state['humid_sensors'])
        self.assertIn('h2', response.state['humid_sensors'])
        self.assertIn('h1', response.humid_sensors)
        self.assertIn('h2', response.humid_sensors)
        self.assertEqual(response.humid_sensors['h1']['corr'], 0.5)
        self.assertEqual(response.humid_sensors['h2']['corr'], -1)

        response = self.webapp_request(h=[['h1', 50], ['h2', 50], ['h3', 50]])  # now adding a new sensor by transmitting it's humidity, the correction should be requested as it's unknown on this one
        self.assertIn('r', response.json)
        self.assertIn(9, response.json['r'])

        response = self.webapp_request(k=[['h3', 2]])
        if 'r' in response.json:
            self.assertNotIn(9, response.json['r'])
        self.assertEqual(len(response.state['humid_sensors']), 3)
        self.assertIn('h1', response.state['humid_sensors'])
        self.assertIn('h2', response.state['humid_sensors'])
        self.assertIn('h3', response.state['humid_sensors'])
        self.assertIn('h1', response.humid_sensors)
        self.assertIn('h2', response.humid_sensors)
        self.assertIn('h3', response.humid_sensors)
        self.assertEqual(response.humid_sensors['h1']['corr'], 0.5)
        self.assertEqual(response.humid_sensors['h2']['corr'], -1)
        self.assertEqual(response.humid_sensors['h3']['corr'], 2)

    def test_max_humid_diff(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        self.assertIn('humid_max_diff', response.state)
        self.assertEqual(response.state['humid_max_diff'], 0)

        response = self.webapp_request(h=[['h1', 54], ['h2', 50]])
        self.assertEqual(response.state['humid_max_diff'], 0)

        response = self.webapp_request(h=[['h1', 55], ['h2', 50]])
        self.assertEqual(response.state['humid_max_diff'], 1)

        response = self.webapp_request(h=[['h1', 55], ['h2', 50.5]])
        self.assertEqual(response.state['humid_max_diff'], 0.5)

        response = self.webapp_request(h=[['h1', 55.75], ['h2', 51]])
        self.assertEqual(response.state['humid_max_diff'], 0.75)

        response = self.webapp_request(h=[['h1', 55], ['h2', 51]])
        self.assertEqual(response.state['humid_max_diff'], 0.75)

        response = self.webapp_request(h=[['h1', 55], ['h2', 50]])
        self.assertEqual(response.state['humid_max_diff'], 1)

        response = self.webapp_request(h=[['h1', 55], ['h2', 50]])
        self.assertEqual(response.state['humid_max_diff'], 0)

    def test_get_humid_sensor(self):  # via AdminInterface
        response = self.webapp_request(clear_state=True, v=self.v, h=[['h1', 50], ['h2', 55]])

        response = self.webapp_request(path='/admin', command='get_humid_sensor', humid_sensor='h1')
        self.assertIn('humid_sensor', response.json)
        self.assertIn('_id', response.json['humid_sensor'])
        self.assertEqual(response.json['humid_sensor']['_id'], 'h1')
        self.assertIn('last_reading', response.json['humid_sensor'])
        self.assertEqual(response.json['humid_sensor']['last_reading'], 50)

        response = self.webapp_request(path='/admin', command='get_humid_sensor', humid_sensor='h2')
        self.assertIn('humid_sensor', response.json)
        self.assertIn('_id', response.json['humid_sensor'])
        self.assertEqual(response.json['humid_sensor']['_id'], 'h2')
        self.assertIn('last_reading', response.json['humid_sensor'])
        self.assertEqual(response.json['humid_sensor']['last_reading'], 55)

    def test_delete_brick_with_sensors(self):
        response = self.webapp_request(clear_state=True, v=self.v, h=[['h1', 50], ['h2', 55]])
        self.assertNotEqual(response.state, {})
        self.assertIn('h1', response.humid_sensors)
        self.assertIn('h2', response.humid_sensors)
        response = self.webapp_request(path="/admin", command='delete_brick', brick='localhost')
        self.assertIn('deleted', response.json)
        self.assertEqual(response.json['deleted']['brick'], 'localhost')
        self.assertIn('h1', response.json['deleted']['humid_sensors'])
        self.assertIn('h2', response.json['deleted']['humid_sensors'])
        self.assertEqual(response.state, {})
        self.assertEqual(response.humid_sensors, {})

    def test_humid_sensor_desc_is_stored(self):
        response = self.webapp_request(clear_state=True, v=self.v, h=[['h1', 50], ['h2', 55]])
        self.assertIsNone(response.humid_sensors['h1']['desc'])
        self.assertIsNone(response.humid_sensors['h2']['desc'])

        response = self.webapp_request(path='/admin', command='set', humid_sensor='h1', key='desc', value='sensor1')
        self.assertEqual(response.json['s'], 0)
        self.assertEqual(response.humid_sensors['h1']['desc'], 'sensor1')
        self.assertIsNone(response.humid_sensors['h2']['desc'])

        response = self.webapp_request(path='/admin', command='set', humid_sensor='h2', key='desc', value='sensor2')
        self.assertEqual(response.json['s'], 0)
        self.assertEqual(response.humid_sensors['h1']['desc'], 'sensor1')
        self.assertEqual(response.humid_sensors['h2']['desc'], 'sensor2')

        response = self.webapp_request(path='/admin', command='set', humid_sensor='h1', key='desc', value='sensorX')
        self.assertEqual(response.json['s'], 0)
        self.assertEqual(response.humid_sensors['h1']['desc'], 'sensorX')
        self.assertEqual(response.humid_sensors['h2']['desc'], 'sensor2')

    def test_valid_values_for_disables(self):
        response = self.webapp_request(clear_state=True, v=self.v, h=[['h1', 50], ['h2', 55]])
        # add disable
        response = self.webapp_request(path='/admin', command='set', humid_sensor='h1', key='add_disable', value='ui')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', humid_sensor='h1', key='add_disable', value='metric')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', humid_sensor='h1', key='add_disable', value='mqtt')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', humid_sensor='h1', key='add_disable', value='invalid')
        self.assertEqual(response.json['s'], 7)
        # del disable
        response = self.webapp_request(path='/admin', command='set', humid_sensor='h1', key='del_disable', value='ui')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', humid_sensor='h1', key='del_disable', value='metric')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', humid_sensor='h1', key='del_disable', value='mqtt')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', humid_sensor='h1', key='del_disable', value='invalid')
        self.assertEqual(response.json['s'], 7)

    def test_disables_are_stored(self):
        response = self.webapp_request(clear_state=True, v=self.v, h=[['h1', 50], ['h2', 55]])
        self.assertEqual(len(response.humid_sensors['h1']['disables']), 0)
        response = self.webapp_request(path='/admin', command='set', humid_sensor='h1', key='add_disable', value='ui')
        self.assertEqual(len(response.humid_sensors['h1']['disables']), 1)
        self.assertIn('ui', response.humid_sensors['h1']['disables'])
        response = self.webapp_request(path='/admin', command='set', humid_sensor='h1', key='add_disable', value='ui')  # no change allready in list
        self.assertEqual(len(response.humid_sensors['h1']['disables']), 1)
        self.assertIn('ui', response.humid_sensors['h1']['disables'])
        response = self.webapp_request(path='/admin', command='set', humid_sensor='h1', key='add_disable', value='metric')
        self.assertEqual(len(response.humid_sensors['h1']['disables']), 2)
        self.assertIn('ui', response.humid_sensors['h1']['disables'])
        self.assertIn('metric', response.humid_sensors['h1']['disables'])
        response = self.webapp_request(path='/admin', command='set', humid_sensor='h1', key='del_disable', value='ui')
        self.assertEqual(len(response.humid_sensors['h1']['disables']), 1)
        self.assertIn('metric', response.humid_sensors['h1']['disables'])
        response = self.webapp_request(path='/admin', command='set', humid_sensor='h1', key='del_disable', value='ui')  # no change allready removed
        self.assertEqual(len(response.humid_sensors['h1']['disables']), 1)
        self.assertIn('metric', response.humid_sensors['h1']['disables'])
        response = self.webapp_request(path='/admin', command='set', humid_sensor='h1', key='del_disable', value='metric')
        self.assertEqual(len(response.humid_sensors['h1']['disables']), 0)

    def test_humid_sensor_count_is_returned(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        response = self.webapp_request(path='/admin', command='get_count', item='humid_sensors')
        self.assertIn('count', response.json)
        self.assertEqual(response.json['count'], 0)
        response = self.webapp_request(h=[['h1', 50], ['h2', 55]])
        response = self.webapp_request(path='/admin', command='get_count', item='humid_sensors')
        self.assertIn('count', response.json)
        self.assertEqual(response.json['count'], 2)
        response = self.webapp_request(h=[['h1', 50], ['h2', 55], ['h3', 60]])
        response = self.webapp_request(path='/admin', command='get_count', item='humid_sensors')
        self.assertIn('count', response.json)
        self.assertEqual(response.json['count'], 3)

    def test_mqtt_messages_are_send(self):
        response = self.webapp_request(clear_state=True, mqtt_test=True, v=self.v, h=[['h1', 50], ['h2', 55]])
        self.assertIn('brick/localhost/humid/h1 50', response.mqtt)
        self.assertIn('brick/localhost/humid/h2 55', response.mqtt)
        response = self.webapp_request(mqtt_test=True, h=[['h1', 50], ['h2', 55], ['h3', 53.5]])
        self.assertIn('brick/localhost/humid/h1 50', response.mqtt)
        self.assertIn('brick/localhost/humid/h2 55', response.mqtt)
        self.assertIn('brick/localhost/humid/h3 53.5', response.mqtt)

        # disableing h2 to send mqtt messages
        response = self.webapp_request(path='/admin', command='set', humid_sensor='h2', key='add_disable', value='mqtt')
        response = self.webapp_request(mqtt_test=True, h=[['h1', 50], ['h2', 55], ['h3', 53.5]])
        self.assertIn('brick/localhost/humid/h1 50', response.mqtt)
        self.assertNotIn('brick/localhost/humid/h2', response.mqtt)
        self.assertIn('brick/localhost/humid/h3 53.5', response.mqtt)

        # enable h2 to send mqtt messages
        response = self.webapp_request(path='/admin', command='set', humid_sensor='h2', key='del_disable', value='mqtt')
        response = self.webapp_request(mqtt_test=True, h=[['h1', 50], ['h2', 55], ['h3', 53.5]])
        self.assertIn('brick/localhost/humid/h1 50', response.mqtt)
        self.assertIn('brick/localhost/humid/h2 55', response.mqtt)
        self.assertIn('brick/localhost/humid/h3 53.5', response.mqtt)
