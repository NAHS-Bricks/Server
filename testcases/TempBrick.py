from ._wrapper import *
from freezegun import freeze_time
from datetime import datetime, timedelta
from helpers.mongodb import brick_exists, temp_sensor_exists

tempbrick_versions = [['os', 1.0], ['all', 1.0], ['bat', 1.0], ['temp', 1.0], ['sleep', 1.0]]


class TestTempBrick(BaseCherryPyTestCase):
    def test_init(self):
        # Newly created brick is initilized
        response = self.webapp_request(clear_state=True, y=['i'])
        self.assertIn('r', response.json)
        self.assertIn(1, response.json['r'])
        self.assertNotIn(3, response.json['r'])
        self.assertNotIn(4, response.json['r'])
        self.assertIn(5, response.json['r'])
        self.assertIn('os', response.state['features'])
        self.assertEqual(response.state['features']['os'], 0)
        self.assertIn('all', response.state['features'])
        self.assertEqual(response.state['features']['all'], 0)
        self.assertEqual(response.state['type'], None)

        # requested data is send over (with versions)
        response = self.webapp_request(v=tempbrick_versions, x=1)
        self.assertIn('r', response.json)
        self.assertIn(3, response.json['r'])
        self.assertEqual(response.state['bat_last_reading'], 0)
        self.assertEqual(response.state['bat_last_ts'], None)
        self.assertIn(6, response.json['r'])
        self.assertEqual(response.state['temp_precision'], None)
        self.assertEqual(response.state['features']['os'], 1.0)
        self.assertEqual(response.state['features']['all'], 1.0)
        self.assertEqual(response.state['features']['temp'], 1.0)
        self.assertEqual(response.state['features']['bat'], 1.0)
        self.assertEqual(response.state['features']['sleep'], 1.0)

        # feature based requested data is send over
        response = self.webapp_request(b=3.7, p=11)
        self.assertEqual(response.state['bat_last_reading'], 3.7)
        self.assertNotEqual(response.state['bat_last_ts'], None)
        self.assertEqual(response.state['temp_precision'], 11)
        self.assertEqual(response.json['s'], 0)

        # An unknown key shouldn't crash the request
        response = self.webapp_request(unknown='something')
        self.assertEqual(response.json['s'], 0)

        # former created brick is initialized
        response = self.webapp_request(y=['i'])
        self.assertIn('r', response.json)
        self.assertIn(1, response.json['r'])
        self.assertNotIn(3, response.json['r'])
        self.assertIn(4, response.json['r'])
        self.assertIn(6, response.json['r'])

    def test_admin_overrides(self):
        response = self.webapp_request(clear_state=True, v=tempbrick_versions)
        response = self.webapp_request(b=3.7, t=[['sensor1', 24]])
        response = self.webapp_request(t=[['sensor1', 24]])
        response = self.webapp_request(path="/admin", command="set", brick="localhost", key="sleep_delay", value=60)
        self.assertIn('admin_override', response.state['features'])
        response = self.webapp_request(t=[['sensor1', 24]])
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 60)
        self.assertNotIn('admin_override', response.state['features'])
        response = self.webapp_request(path="/admin", command="set", brick="localhost", key="bat_voltage", value=True)
        self.assertIn('admin_override', response.state['features'])
        response = self.webapp_request(t=[['sensor1', 24]])
        self.assertIn('r', response.json)
        self.assertIn(3, response.json['r'])
        self.assertNotIn('admin_override', response.state['features'])
        # combined:
        response = self.webapp_request(path="/admin", command="set", brick="localhost", key="sleep_delay", value=60)
        response = self.webapp_request(path="/admin", command="set", brick="localhost", key="bat_voltage", value=True)
        self.assertIn('admin_override', response.state['features'])
        response = self.webapp_request(t=[['sensor1', 24]])
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 60)
        self.assertIn('r', response.json)
        self.assertIn(3, response.json['r'])
        self.assertNotIn('admin_override', response.state['features'])
        # update temp_precision
        response = self.webapp_request(path="/admin", command="set", brick="localhost", key="temp_precision", value=9)
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(t=[['sensor1', 24]])
        self.assertEqual(response.json['p'], 9)
        response = self.webapp_request(path="/admin", command="set", brick="localhost", key="temp_precision", value=12)
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(t=[['sensor1', 24]])
        self.assertEqual(response.json['p'], 12)
        response = self.webapp_request(path="/admin", command="set", brick="localhost", key="temp_precision", value=8)
        self.assertEqual(response.json['s'], 7)
        response = self.webapp_request(t=[['sensor1', 24]])
        self.assertNotIn('p', response.json)
        response = self.webapp_request(path="/admin", command="set", brick="localhost", key="temp_precision", value=13)
        self.assertEqual(response.json['s'], 7)
        response = self.webapp_request(t=[['sensor1', 24]])
        self.assertNotIn('p', response.json)

    def test_admin_delete_brick(self):
        response = self.webapp_request(clear_state=True, v=tempbrick_versions)
        response = self.webapp_request(b=3.7, t=[['sensor1', 24], ['sensor2', 24.1]])
        self.assertEqual(brick_exists('localhost'), True)
        self.assertEqual(temp_sensor_exists('sensor1'), True)
        self.assertEqual(temp_sensor_exists('sensor2'), True)
        response = self.webapp_request(path="/admin", command="delete_brick", brick="localhost2")  # Invalid Brick (should change nothing)
        self.assertEqual(response.json['s'], 3)  # Invalid Brick returncode
        self.assertEqual(brick_exists('localhost'), True)
        self.assertEqual(temp_sensor_exists('sensor1'), True)
        self.assertEqual(temp_sensor_exists('sensor2'), True)
        response = self.webapp_request(path="/admin", command="delete_brick", brick="localhost")
        self.assertIn('deleted', response.json)
        self.assertIn('brick', response.json['deleted'])
        self.assertIn('temp_sensors', response.json['deleted'])
        self.assertEqual(response.json['deleted']['brick'], 'localhost')
        self.assertIn('sensor1', response.json['deleted']['temp_sensors'])
        self.assertIn('sensor2', response.json['deleted']['temp_sensors'])
        self.assertEqual(brick_exists('localhost'), False)
        self.assertEqual(temp_sensor_exists('sensor1'), False)
        self.assertEqual(temp_sensor_exists('sensor2'), False)

    def test_periodic_bat_voltage_request(self):
        time_now = datetime.now()
        time_13_hours_ago = time_now - timedelta(hours=13)
        time_14_hours_ago = time_now - timedelta(hours=14)
        with freeze_time(time_14_hours_ago):
            response = self.webapp_request(clear_state=True, v=tempbrick_versions)
            response = self.webapp_request(b=3.7, t=[['sensor1', 24]])
            response = self.webapp_request(t=[['sensor1', 24]])
            if 'r' in response.json:
                self.assertNotIn(3, response.json['r'])
        with freeze_time(time_13_hours_ago):
            response = self.webapp_request(t=[['sensor1', 24]])
            if 'r' in response.json:
                self.assertNotIn(3, response.json['r'])
        with freeze_time(time_now):
            response = self.webapp_request(t=[['sensor1', 24]])
            self.assertIn('r', response.json)
            self.assertIn(3, response.json['r'])

    def test_sensor_corr(self):
        response = self.webapp_request(clear_state=True, v=tempbrick_versions)
        if 'r' in response.json:
            self.assertNotIn(4, response.json['r'])
        response = self.webapp_request(t=[['sensor1', 24], ['sensor2', 25]])
        self.assertIn('sensor1', response.state['temp_sensors'])
        self.assertIn('sensor2', response.state['temp_sensors'])
        self.assertIn('sensor1', response.temp_sensors)
        self.assertEqual(response.temp_sensors['sensor1']['corr'], None)
        self.assertIn('sensor2', response.temp_sensors)
        self.assertEqual(response.temp_sensors['sensor2']['corr'], None)
        self.assertIn('r', response.json)
        self.assertIn(4, response.json['r'])

        response = self.webapp_request(c=[['sensor1', 0], ['sensor2', -0.1]])
        self.assertEqual(response.temp_sensors['sensor1']['corr'], 0)
        self.assertEqual(response.temp_sensors['sensor2']['corr'], -0.1)
        if 'r' in response.json:
            self.assertNotIn(4, response.json['r'])
