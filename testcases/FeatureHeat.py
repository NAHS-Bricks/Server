from ._wrapper import *


@parameterized_class(getVersionParameter('heat'))
class TestFeatureHeat(BaseCherryPyTestCase):
    def test_temperatures_are_stored(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        self.assertIn('temp_sensors', response.state)
        self.assertEqual(len(response.state['temp_sensors']), 0)

        response = self.webapp_request(t=[['localhost_rad', 24]])
        self.assertEqual(len(response.state['temp_sensors']), 1)
        self.assertIn('localhost_rad', response.state['temp_sensors'])
        self.assertIn('localhost_rad', response.temp_sensors)
        self.assertEqual(response.temp_sensors['localhost_rad']['last_reading'], 24)

        response = self.webapp_request(t=[['localhost_rad', 25]])
        self.assertEqual(len(response.state['temp_sensors']), 1)
        self.assertIn('localhost_rad', response.state['temp_sensors'])
        self.assertIn('localhost_rad', response.temp_sensors)
        self.assertEqual(response.temp_sensors['localhost_rad']['last_reading'], 25)
        self.assertEqual(response.temp_sensors['localhost_rad']['prev_reading'], 24)

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

        response = self.webapp_request(c=[['localhost_rad', 1]])
        if 'r' in response.json:
            self.assertNotIn(4, response.json['r'])
        self.assertEqual(len(response.state['temp_sensors']), 1)
        self.assertIn('localhost_rad', response.state['temp_sensors'])
        self.assertIn('localhost_rad', response.temp_sensors)
        self.assertEqual(response.temp_sensors['localhost_rad']['corr'], 1)

        response = self.webapp_request(c=[['localhost_rad', 0.5]])
        if 'r' in response.json:
            self.assertNotIn(4, response.json['r'])
        self.assertEqual(len(response.state['temp_sensors']), 1)
        self.assertIn('localhost_rad', response.state['temp_sensors'])
        self.assertIn('localhost_rad', response.temp_sensors)
        self.assertEqual(response.temp_sensors['localhost_rad']['corr'], 0.5)

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

        response = self.webapp_request(t=[['localhost_rad', 25]])
        self.assertEqual(response.state['temp_max_diff'], 0)

        response = self.webapp_request(t=[['localhost_rad', 26]])
        self.assertEqual(response.state['temp_max_diff'], 1)

        response = self.webapp_request(t=[['localhost_rad', 26.75]])
        self.assertEqual(response.state['temp_max_diff'], 0.75)

        response = self.webapp_request(t=[['localhost_rad', 25]])
        self.assertEqual(response.state['temp_max_diff'], 1.75)

        response = self.webapp_request(t=[['localhost_rad', 25]])
        self.assertEqual(response.state['temp_max_diff'], 0)

    def test_get_temp_sensor(self):  # via AdminInterface
        response = self.webapp_request(clear_state=True, v=self.v, t=[['localhost_rad', 22]])

        response = self.webapp_request(path='/admin', command='get_temp_sensor', temp_sensor='localhost_rad')
        self.assertIn('temp_sensor', response.json)
        self.assertIn('_id', response.json['temp_sensor'])
        self.assertEqual(response.json['temp_sensor']['_id'], 'localhost_rad')
        self.assertIn('last_reading', response.json['temp_sensor'])
        self.assertEqual(response.json['temp_sensor']['last_reading'], 22)

    def test_delete_brick_with_sensors_and_heater(self):
        response = self.webapp_request(clear_state=True, v=self.v, t=[['localhost_rad', 24]])
        self.assertNotEqual(str(response.state), '{}')
        self.assertEqual(len(response.temp_sensors), 1)
        self.assertEqual(len(response.heaters), 1)
        self.assertIn('localhost_rad', response.temp_sensors)
        self.assertIn('localhost', response.heaters)
        response = self.webapp_request(path="/admin", command='delete_brick', brick='localhost')
        self.assertIn('deleted', response.json)
        self.assertEqual(response.json['deleted']['brick'], 'localhost')
        self.assertIn('localhost_rad', response.json['deleted']['temp_sensors'])
        self.assertIn('localhost', response.json['deleted']['heaters'])
        self.assertEqual(str(response.state), '{}')
        self.assertEqual(len(response.temp_sensors), 0)
        self.assertEqual(len(response.heaters), 0)

    def test_temp_sensor_desc_is_stored(self):
        response = self.webapp_request(clear_state=True, v=self.v, t=[['localhost_rad', 24]])
        self.assertIsNone(response.temp_sensors['localhost_rad']['desc'])

        response = self.webapp_request(path='/admin', command='set', temp_sensor='localhost_rad', key='desc', value='sensor1')
        self.assertEqual(response.json['s'], 0)
        self.assertEqual(response.temp_sensors['localhost_rad']['desc'], 'sensor1')

        response = self.webapp_request(path='/admin', command='set', temp_sensor='localhost_rad', key='desc', value='sensorX')
        self.assertEqual(response.json['s'], 0)
        self.assertEqual(response.temp_sensors['localhost_rad']['desc'], 'sensorX')

    def test_temp_valid_values_for_disables(self):
        response = self.webapp_request(clear_state=True, v=self.v, t=[['localhost_rad', 24]])
        # add disable
        response = self.webapp_request(path='/admin', command='set', temp_sensor='localhost_rad', key='add_disable', value='ui')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', temp_sensor='localhost_rad', key='add_disable', value='metric')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', temp_sensor='localhost_rad', key='add_disable', value='invalid')
        self.assertEqual(response.json['s'], 7)
        # del disable
        response = self.webapp_request(path='/admin', command='set', temp_sensor='localhost_rad', key='del_disable', value='ui')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', temp_sensor='localhost_rad', key='del_disable', value='metric')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', temp_sensor='localhost_rad', key='del_disable', value='invalid')
        self.assertEqual(response.json['s'], 7)

    def test_temp_disables_are_stored(self):
        response = self.webapp_request(clear_state=True, v=self.v, t=[['localhost_rad', 24]])
        self.assertEqual(len(response.temp_sensors['localhost_rad']['disables']), 0)
        response = self.webapp_request(path='/admin', command='set', temp_sensor='localhost_rad', key='add_disable', value='ui')
        self.assertEqual(len(response.temp_sensors['localhost_rad']['disables']), 1)
        self.assertIn('ui', response.temp_sensors['localhost_rad']['disables'])
        response = self.webapp_request(path='/admin', command='set', temp_sensor='localhost_rad', key='add_disable', value='ui')  # no change allready in list
        self.assertEqual(len(response.temp_sensors['localhost_rad']['disables']), 1)
        self.assertIn('ui', response.temp_sensors['localhost_rad']['disables'])
        response = self.webapp_request(path='/admin', command='set', temp_sensor='localhost_rad', key='add_disable', value='metric')
        self.assertEqual(len(response.temp_sensors['localhost_rad']['disables']), 2)
        self.assertIn('ui', response.temp_sensors['localhost_rad']['disables'])
        self.assertIn('metric', response.temp_sensors['localhost_rad']['disables'])
        response = self.webapp_request(path='/admin', command='set', temp_sensor='localhost_rad', key='del_disable', value='ui')
        self.assertEqual(len(response.temp_sensors['localhost_rad']['disables']), 1)
        self.assertIn('metric', response.temp_sensors['localhost_rad']['disables'])
        response = self.webapp_request(path='/admin', command='set', temp_sensor='localhost_rad', key='del_disable', value='ui')  # no change allready removed
        self.assertEqual(len(response.temp_sensors['localhost_rad']['disables']), 1)
        self.assertIn('metric', response.temp_sensors['localhost_rad']['disables'])
        response = self.webapp_request(path='/admin', command='set', temp_sensor='localhost_rad', key='del_disable', value='metric')
        self.assertEqual(len(response.temp_sensors['localhost_rad']['disables']), 0)

    def test_temp_sensor_count_is_returned(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        response = self.webapp_request(path='/admin', command='get_count', item='temp_sensors')
        self.assertIn('count', response.json)
        self.assertEqual(response.json['count'], 0)
        response = self.webapp_request(t=[['localhost_rad', 24]])
        response = self.webapp_request(path='/admin', command='get_count', item='temp_sensors')
        self.assertIn('count', response.json)
        self.assertEqual(response.json['count'], 1)

    def test_temp_mqtt_messages_are_send(self):
        response = self.webapp_request(clear_state=True, mqtt_test=True, v=self.v, t=[['localhost_rad', 25]])
        self.assertIn('brick/localhost/temp/localhost_rad 25', response.mqtt)
        response = self.webapp_request(mqtt_test=True, t=[['localhost_rad', 24]])
        self.assertIn('brick/localhost/temp/localhost_rad 24', response.mqtt)

        # disableing s2 to send mqtt messages
        response = self.webapp_request(path='/admin', command='set', temp_sensor='localhost_rad', key='add_disable', value='mqtt')
        response = self.webapp_request(mqtt_test=True, t=[['localhost_rad', 25]])
        self.assertNotIn('brick/localhost/temp/localhost_rad 25', response.mqtt)

        # enable s2 to send mqtt messages
        response = self.webapp_request(path='/admin', command='set', temp_sensor='localhost_rad', key='del_disable', value='mqtt')
        response = self.webapp_request(mqtt_test=True, t=[['localhost_rad', 25]])
        self.assertIn('brick/localhost/temp/localhost_rad 25', response.mqtt)

    def test_heater_created_on_brick_creation(self):
        # after the feature heat is recognized on a brick, a heater should be auto created for this brick
        response = self.webapp_request(clear_state=True)  # Create Brick without features, no heater should exist
        self.assertEqual(len(response.heaters), 0)

        response = self.webapp_request(v=self.v)  # Now transmit versions, the heater should be auto-created
        self.assertEqual(len(response.heaters), 1)
        self.assertIn('localhost', response.heaters)

    def test_heater_set_state_api(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        self.assertEqual(response.heaters['localhost']['state'], 0)
        self.assertIsNone(response.heaters['localhost']['state_set_ts'])
        self.assertIsNone(response.heaters['localhost']['state_transmitted_ts'])

        response = self.webapp_request(path='/admin', command='set', key='heater', heater='localhost', value=1)
        self.assertEqual(response.heaters['localhost']['state'], 1)
        self.assertIsNotNone(response.heaters['localhost']['state_set_ts'])
        self.assertIsNone(response.heaters['localhost']['state_transmitted_ts'])

        response = self.webapp_request(path='/admin', command='set', key='heater', heater='localhost', value=0)
        self.assertEqual(response.heaters['localhost']['state'], 0)
        self.assertIsNotNone(response.heaters['localhost']['state_set_ts'])
        self.assertIsNone(response.heaters['localhost']['state_transmitted_ts'])

        # invalid heater
        response = self.webapp_request(path='/admin', command='set', key='heater', heater='localhost_2', value=1)
        self.assertEqual(response.json['s'], 44)

        # invalid values
        response = self.webapp_request(path='/admin', command='set', key='heater', heater='localhost', value=-1)
        self.assertEqual(response.json['s'], 7)
        response = self.webapp_request(path='/admin', command='set', key='heater', heater='localhost', value=2)
        self.assertEqual(response.json['s'], 7)

    def test_heater_states_are_transmitted(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        self.assertNotIn('h', response.json)
        self.assertIsNone(response.heaters['localhost']['state_transmitted_ts'])

        response = self.webapp_request(y=['i'])
        self.assertIn('h', response.json)
        self.assertEqual(response.json['h'], 0)
        self.assertIsNotNone(response.heaters['localhost']['state_transmitted_ts'])

        response = self.webapp_request(path='/admin', command='set', key='heater', heater='localhost', value=1)
        self.assertIsNone(response.heaters['localhost']['state_transmitted_ts'])
        response = self.webapp_request()
        self.assertIn('h', response.json)
        self.assertEqual(response.json['h'], 1)
        self.assertIsNotNone(response.heaters['localhost']['state_transmitted_ts'])

        response = self.webapp_request(path='/admin', command='set', key='heater', heater='localhost', value=0)
        self.assertIsNone(response.heaters['localhost']['state_transmitted_ts'])
        response = self.webapp_request()
        self.assertIn('h', response.json)
        self.assertEqual(response.json['h'], 0)
        self.assertIsNotNone(response.heaters['localhost']['state_transmitted_ts'])

    def test_heater_desc_is_stored(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        self.assertIsNone(response.heaters['localhost']['desc'])

        response = self.webapp_request(path='/admin', command='set', heater='localhost', key='desc', value='heat1')
        self.assertEqual(response.json['s'], 0)
        self.assertEqual(response.heaters['localhost']['desc'], 'heat1')

        response = self.webapp_request(path='/admin', command='set', heater='localhost', key='desc', value='heatX')
        self.assertEqual(response.json['s'], 0)
        self.assertEqual(response.heaters['localhost']['desc'], 'heatX')

    def test_get_heater(self):  # via AdminInterface
        response = self.webapp_request(clear_state=True, v=self.v)
        response = self.webapp_request(path='/admin', command='get_heater', heater='localhost')
        self.assertIn('heater', response.json)
        self.assertIn('_id', response.json['heater'])
        self.assertEqual(response.json['heater']['_id'], 'localhost')
        self.assertEqual(response.json['heater']['state'], 0)
        self.assertIsNone(response.json['heater']['desc'])

        response = self.webapp_request(path='/admin', command='set', key='heater', heater='localhost', value=1)
        response = self.webapp_request(path='/admin', command='set', heater='localhost', key='desc', value='heat1')

        response = self.webapp_request(path='/admin', command='get_heater', heater='localhost')
        self.assertIn('heater', response.json)
        self.assertIn('_id', response.json['heater'])
        self.assertEqual(response.json['heater']['_id'], 'localhost')
        self.assertEqual(response.json['heater']['state'], 1)
        self.assertEqual(response.json['heater']['desc'], 'heat1')

    def test_heater_valid_state_desc_states(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        response = self.webapp_request(path="/admin", command='set', heater='localhost', key='state_desc', state=-1, value='not used')
        self.assertEqual(response.json['s'], 7)
        response = self.webapp_request(path="/admin", command='set', heater='localhost', key='state_desc', state=0, value='not used')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path="/admin", command='set', heater='localhost', key='state_desc', state=1, value='not used')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path="/admin", command='set', heater='localhost', key='state_desc', state=2, value='not used')
        self.assertEqual(response.json['s'], 7)

    def test_heater_state_desc_is_stored(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        self.assertEqual(response.heaters['localhost']['states_desc'][0], 'off')
        self.assertEqual(response.heaters['localhost']['states_desc'][1], 'on')
        response = self.webapp_request(path="/admin", command='set', heater='localhost', key='state_desc', state=0, value='state1')
        self.assertEqual(response.heaters['localhost']['states_desc'][0], 'state1')
        self.assertEqual(response.heaters['localhost']['states_desc'][1], 'on')
        response = self.webapp_request(path="/admin", command='set', heater='localhost', key='state_desc', state=1, value='state2')
        self.assertEqual(response.heaters['localhost']['states_desc'][0], 'state1')
        self.assertEqual(response.heaters['localhost']['states_desc'][1], 'state2')

    def test_heater_valid_values_for_disables(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        # add disable
        response = self.webapp_request(path='/admin', command='set', heater='localhost', key='add_disable', value='ui')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', heater='localhost', key='add_disable', value='metric')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', heater='localhost', key='add_disable', value='mqtt')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', heater='localhost', key='add_disable', value='invalid')
        self.assertEqual(response.json['s'], 7)
        # del disable
        response = self.webapp_request(path='/admin', command='set', heater='localhost', key='del_disable', value='ui')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', heater='localhost', key='del_disable', value='metric')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', heater='localhost', key='del_disable', value='mqtt')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', heater='localhost', key='del_disable', value='invalid')
        self.assertEqual(response.json['s'], 7)

    def test_heater_disables_are_stored(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        self.assertEqual(len(response.heaters['localhost']['disables']), 0)  # nothing present by default
        response = self.webapp_request(path='/admin', command='set', heater='localhost', key='add_disable', value='ui')
        self.assertEqual(len(response.heaters['localhost']['disables']), 1)
        self.assertIn('ui', response.heaters['localhost']['disables'])
        response = self.webapp_request(path='/admin', command='set', heater='localhost', key='add_disable', value='ui')  # no change allready in list
        self.assertEqual(len(response.heaters['localhost']['disables']), 1)
        self.assertIn('ui', response.heaters['localhost']['disables'])
        response = self.webapp_request(path='/admin', command='set', heater='localhost', key='add_disable', value='metric')
        self.assertEqual(len(response.heaters['localhost']['disables']), 2)
        self.assertIn('ui', response.heaters['localhost']['disables'])
        self.assertIn('metric', response.heaters['localhost']['disables'])
        response = self.webapp_request(path='/admin', command='set', heater='localhost', key='add_disable', value='mqtt')
        self.assertEqual(len(response.heaters['localhost']['disables']), 3)
        response = self.webapp_request(path='/admin', command='set', heater='localhost', key='add_disable', value='mqtt')  # no change allready in list
        self.assertEqual(len(response.heaters['localhost']['disables']), 3)
        self.assertIn('ui', response.heaters['localhost']['disables'])
        self.assertIn('metric', response.heaters['localhost']['disables'])
        self.assertIn('mqtt', response.heaters['localhost']['disables'])
        response = self.webapp_request(path='/admin', command='set', heater='localhost', key='del_disable', value='ui')
        self.assertEqual(len(response.heaters['localhost']['disables']), 2)
        self.assertIn('metric', response.heaters['localhost']['disables'])
        self.assertIn('mqtt', response.heaters['localhost']['disables'])
        response = self.webapp_request(path='/admin', command='set', heater='localhost', key='del_disable', value='ui')  # no change allready removed
        self.assertEqual(len(response.heaters['localhost']['disables']), 2)
        self.assertIn('metric', response.heaters['localhost']['disables'])
        self.assertIn('mqtt', response.heaters['localhost']['disables'])
        response = self.webapp_request(path='/admin', command='set', heater='localhost', key='del_disable', value='mqtt')
        self.assertEqual(len(response.heaters['localhost']['disables']), 1)
        self.assertIn('metric', response.heaters['localhost']['disables'])
        response = self.webapp_request(path='/admin', command='set', heater='localhost', key='del_disable', value='metric')
        self.assertEqual(len(response.heaters['localhost']['disables']), 0)

    def test_heater_mqtt_messages_are_send(self):
        response = self.webapp_request(clear_state=True, mqtt_test=True, v=self.v)
        self.assertNotIn('brick/localhost/heater', response.mqtt)

        response = self.webapp_request(mqtt_test=True, y=['i'])
        self.assertIn('brick/localhost/heater 0', response.mqtt)

        response = self.webapp_request(mqtt_test=True, path='/admin', command='set', key='heater', heater='localhost', value=1)
        self.assertIn('brick/localhost/heater 11', response.mqtt)
        response = self.webapp_request(mqtt_test=True)
        self.assertIn('brick/localhost/heater 1', response.mqtt)

        response = self.webapp_request(mqtt_test=True, path='/admin', command='set', key='heater', heater='localhost', value=0)
        self.assertIn('brick/localhost/heater 10', response.mqtt)
        response = self.webapp_request(mqtt_test=True)
        self.assertIn('brick/localhost/heater 0', response.mqtt)

        # disable heater to send mqtt messages
        response = self.webapp_request(path='/admin', command='set', heater='localhost', key='add_disable', value='mqtt')
        response = self.webapp_request(mqtt_test=True, path='/admin', command='set', key='heater', heater='localhost', value=1)
        self.assertNotIn('brick/localhost/heater', response.mqtt)
        response = self.webapp_request(mqtt_test=True)
        self.assertNotIn('brick/localhost/heater 1', response.mqtt)

        # reanable heater to send mqtt messages
        response = self.webapp_request(path='/admin', command='set', heater='localhost', key='del_disable', value='mqtt')
        response = self.webapp_request(mqtt_test=True, path='/admin', command='set', key='heater', heater='localhost', value=1)
        self.assertIn('brick/localhost/heater', response.mqtt)
        response = self.webapp_request(mqtt_test=True)
        self.assertIn('brick/localhost/heater 1', response.mqtt)

    def test_heater_metrics_are_stored(self):
        sel_stmt = 'SELECT "state" FROM "brickserver"."8weeks"."heaters" WHERE "brick_id" = \'localhost\' and "heater_id" = \'localhost\' ORDER BY time DESC LIMIT 1'
        sel_stmt_d = 'SELECT "state" FROM "brickserver"."8weeks"."heaters" WHERE "brick_desc" = \'b1\' and "heater_desc" = \'h1\' ORDER BY time DESC LIMIT 1'
        response = self.webapp_request(clear_state=True, clear_influx=True, v=self.v)
        response = self.webapp_request(path='/admin', command='set', heater='localhost', key='del_disable', value='metric')
        response = self.webapp_request(path='/admin', command='set', key='desc', brick='localhost', value='b1')
        response = self.webapp_request(path='/admin', command='set', key='desc', heater='localhost', value='h1')

        response = self.webapp_request(path='/admin', command='set', key='heater', heater='localhost', value=0)
        response = self.webapp_request()
        time.sleep(0.05)
        self.assertEqual(influxDB.query(sel_stmt).raw['series'][0]['values'][0][1], 0)
        # metrics should also be found with their description
        self.assertEqual(influxDB.query(sel_stmt_d).raw['series'][0]['values'][0][1], 0)

        response = self.webapp_request(path='/admin', command='set', key='heater', heater='localhost', value=1)
        response = self.webapp_request()
        time.sleep(0.05)
        self.assertEqual(influxDB.query(sel_stmt).raw['series'][0]['values'][0][1], 1)
        # metrics should also be found with their description
        self.assertEqual(influxDB.query(sel_stmt_d).raw['series'][0]['values'][0][1], 1)

        response = self.webapp_request(path='/admin', command='set', key='heater', heater='localhost', value=0)
        response = self.webapp_request(mqtt_test=True)  # mqtt_test is just to be sure the queue is clean for following tests
        time.sleep(0.05)
        self.assertEqual(influxDB.query(sel_stmt).raw['series'][0]['values'][0][1], 0)
        # metrics should also be found with their description
        self.assertEqual(influxDB.query(sel_stmt_d).raw['series'][0]['values'][0][1], 0)
