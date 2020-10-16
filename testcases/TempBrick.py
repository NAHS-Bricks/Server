from ._wrapper import *
from freezegun import freeze_time
from datetime import datetime, timedelta

tempbrick_features = ['bat', 'temp', 'sleep']


class TestTempBrick(BaseCherryPyTestCase):
    def test_init(self):
        response = self.webapp_request(clear_state=True, y=['i'])
        self.assertIn('r', response.json)
        self.assertIn(1, response.json['r'])
        self.assertIn(2, response.json['r'])
        self.assertEqual(response.state['features'], [])
        self.assertEqual(response.state['version'], None)

        response = self.webapp_request(v='1.0', f=tempbrick_features)
        self.assertIn('r', response.json)
        self.assertIn(3, response.json['r'])
        self.assertEqual(response.state['version'], '1.0')
        self.assertIn('temp', response.state['features'])
        self.assertIn('bat', response.state['features'])
        self.assertIn('sleep', response.state['features'])
        self.assertEqual(response.state['bat_last_reading'], 0)
        self.assertEqual(response.state['bat_last_ts'], None)

        response = self.webapp_request(b=3.7)
        self.assertEqual(response.state['bat_last_reading'], 3.7)
        self.assertNotEqual(response.state['bat_last_ts'], None)
        self.assertEqual(response.json, {'s': 0})

        response = self.webapp_request(unknown='something')  # An unknown key shouldn't crash the request
        self.assertEqual(response.json['s'], 0)

    def test_sleep_delay_increase(self):
        response = self.webapp_request(clear_state=True, v='1.0', f=tempbrick_features)
        response = self.webapp_request(b=3.7, t=[['sensor1', 25]])
        response = self.webapp_request(t=[['sensor1', 24]])
        self.assertEqual(response.state['sleep_delay'], 60)
        self.assertEqual(response.state['sleep_increase_wait'], 3)
        response = self.webapp_request(t=[['sensor1', 24]])
        self.assertEqual(response.state['sleep_increase_wait'], 2)
        response = self.webapp_request(t=[['sensor1', 24]])
        self.assertEqual(response.state['sleep_increase_wait'], 1)
        response = self.webapp_request(t=[['sensor1', 24]])
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 120)
        self.assertEqual(response.state['sleep_delay'], 120)
        self.assertEqual(response.state['sleep_increase_wait'], 3)
        response = self.webapp_request(t=[['sensor1', 24]])
        self.assertEqual(response.state['sleep_increase_wait'], 2)
        response = self.webapp_request(t=[['sensor1', 24]])
        self.assertEqual(response.state['sleep_increase_wait'], 1)
        response = self.webapp_request(t=[['sensor1', 24]])
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 180)
        self.assertEqual(response.state['sleep_delay'], 180)
        self.assertEqual(response.state['sleep_increase_wait'], 3)
        response = self.webapp_request(t=[['sensor1', 24]])
        self.assertEqual(response.state['sleep_increase_wait'], 2)
        response = self.webapp_request(t=[['sensor1', 24]])
        self.assertEqual(response.state['sleep_increase_wait'], 1)
        response = self.webapp_request(t=[['sensor1', 24]])
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 240)
        self.assertEqual(response.state['sleep_delay'], 240)
        self.assertEqual(response.state['sleep_increase_wait'], 3)
        response = self.webapp_request(t=[['sensor1', 24]])
        self.assertEqual(response.state['sleep_increase_wait'], 2)
        response = self.webapp_request(t=[['sensor1', 24]])
        self.assertEqual(response.state['sleep_increase_wait'], 1)
        response = self.webapp_request(t=[['sensor1', 24]])
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 300)
        self.assertEqual(response.state['sleep_delay'], 300)
        self.assertEqual(response.state['sleep_increase_wait'], 3)
        response = self.webapp_request(t=[['sensor1', 24]])
        self.assertEqual(response.state['sleep_increase_wait'], 2)
        response = self.webapp_request(t=[['sensor1', 24]])
        self.assertEqual(response.state['sleep_increase_wait'], 1)
        response = self.webapp_request(t=[['sensor1', 24]])
        self.assertEqual(response.state['sleep_increase_wait'], 0)
        response = self.webapp_request(t=[['sensor1', 24]])
        self.assertEqual(response.state['sleep_increase_wait'], 0)

    def test_sleep_delay_decrease(self):
        response = self.webapp_request(clear_state=True, v='1.0', f=tempbrick_features)
        response = self.webapp_request(b=3.7)
        response = self.webapp_request(t=[['sensor1', 24]])
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 120)
        self.assertEqual(response.state['sleep_delay'], 120)
        self.assertEqual(response.state['sleep_increase_wait'], 3)
        response = self.webapp_request(t=[['sensor1', 25]])
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 60)
        self.assertEqual(response.state['sleep_delay'], 60)
        self.assertEqual(response.state['sleep_increase_wait'], 3)
        response = self.webapp_request(t=[['sensor1', 25]])
        self.assertNotIn('d', response.json)
        self.assertEqual(response.state['sleep_delay'], 60)
        self.assertEqual(response.state['sleep_increase_wait'], 2)
        response = self.webapp_request(t=[['sensor1', 26]])
        self.assertNotIn('d', response.json)
        self.assertEqual(response.state['sleep_delay'], 60)
        self.assertEqual(response.state['sleep_increase_wait'], 3)

    def test_charging(self):
        response = self.webapp_request(clear_state=True, v='1.0', f=tempbrick_features)
        response = self.webapp_request(b=3.7, t=[['sensor1', 24]])
        self.assertNotIn('Charge bat on', response.telegram)
        response = self.webapp_request(b=3.4, t=[['sensor1', 24]])
        self.assertIn('Charge bat on', response.telegram)
        self.assertEqual(response.state['bat_last_reading'], 3.4)
        self.assertEqual(response.state['bat_charging'], False)
        self.assertEqual(response.state['bat_charging_standby'], False)
        response = self.webapp_request(y=['c'], t=[['sensor1', 24]])
        self.assertEqual(response.state['bat_charging'], True)
        self.assertEqual(response.state['bat_charging_standby'], False)
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 60)
        response = self.webapp_request(y=['c'], t=[['sensor1', 24]])
        response = self.webapp_request(y=['c'], t=[['sensor1', 24]])
        response = self.webapp_request(y=['c'], t=[['sensor1', 24]])
        self.assertEqual(response.state['bat_charging'], True)
        self.assertEqual(response.state['bat_charging_standby'], False)
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 60)
        response = self.webapp_request(y=['s'], t=[['sensor1', 24]])
        self.assertEqual(response.state['bat_charging'], False)
        self.assertEqual(response.state['bat_charging_standby'], True)
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 60)
        self.assertIn('r', response.json)
        self.assertIn(3, response.json['r'])
        response = self.webapp_request(y=['s'], t=[['sensor1', 24]])
        self.assertEqual(response.state['bat_charging'], False)
        self.assertEqual(response.state['bat_charging_standby'], True)
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 60)
        self.assertNotIn('r', response.json)
        response = self.webapp_request(y=[], t=[['sensor1', 24]])
        self.assertEqual(response.state['bat_charging'], False)
        self.assertEqual(response.state['bat_charging_standby'], False)
        self.assertNotIn('d', response.json)
        self.assertIn('r', response.json)
        self.assertIn(3, response.json['r'])
        response = self.webapp_request(y=[], t=[['sensor1', 24]])
        self.assertEqual(response.state['bat_charging'], False)
        self.assertEqual(response.state['bat_charging_standby'], False)
        self.assertNotIn('d', response.json)
        self.assertNotIn('r', response.json)

    def test_admin_overrides(self):
        response = self.webapp_request(clear_state=True, v='1.0', f=tempbrick_features)
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
        self.assertEqual(response.json['s'], 5)
        response = self.webapp_request(t=[['sensor1', 24]])
        self.assertNotIn('p', response.json)
        response = self.webapp_request(path="/admin", command="set", brick="localhost", key="temp_precision", value=13)
        self.assertEqual(response.json['s'], 5)
        response = self.webapp_request(t=[['sensor1', 24]])
        self.assertNotIn('p', response.json)

    def test_without_features(self):
        response = self.webapp_request(clear_state=True, v='1.0', f=[])
        response = self.webapp_request(b=3.7, t=[['sensor1', 24]])
        self.assertEqual(response.json, {'s': 0})

    def test_periodic_bat_voltage_request(self):
        time_now = datetime.now()
        time_13_hours_ago = time_now - timedelta(hours=13)
        time_14_hours_ago = time_now - timedelta(hours=14)
        with freeze_time(time_14_hours_ago):
            response = self.webapp_request(clear_state=True, v='1.0', f=tempbrick_features)
            response = self.webapp_request(b=3.7, t=[['sensor1', 24]])
            response = self.webapp_request(t=[['sensor1', 24]])
            self.assertNotIn('r', response.json)
        with freeze_time(time_13_hours_ago):
            response = self.webapp_request(t=[['sensor1', 24]])
            self.assertNotIn('r', response.json)
        with freeze_time(time_now):
            response = self.webapp_request(t=[['sensor1', 24]])
            self.assertIn('r', response.json)
            self.assertIn(3, response.json['r'])
