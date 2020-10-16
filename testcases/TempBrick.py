from ._wrapper import *
from freezegun import freeze_time
from datetime import datetime, timedelta

tempbrick_features = ['bat', 'temp', 'sleep']


class TestTempBrick(BaseCherryPyTestCase):
    def test_init(self):
        # Newly created brick is initilized
        response = self.webapp_request(clear_state=True, y=['i'])
        self.assertIn('r', response.json)
        self.assertIn(1, response.json['r'])
        self.assertIn(2, response.json['r'])
        self.assertNotIn(3, response.json['r'])
        self.assertNotIn(4, response.json['r'])
        self.assertEqual(response.state['features'], [])
        self.assertEqual(response.state['version'], None)

        # requested data is send over
        response = self.webapp_request(v='1.0', f=tempbrick_features)
        self.assertIn('r', response.json)
        self.assertIn(3, response.json['r'])
        self.assertEqual(response.state['version'], '1.0')
        self.assertIn('temp', response.state['features'])
        self.assertIn('bat', response.state['features'])
        self.assertIn('sleep', response.state['features'])
        self.assertEqual(response.state['bat_last_reading'], 0)
        self.assertEqual(response.state['bat_last_ts'], None)

        # feature based requested data is send over
        response = self.webapp_request(b=3.7)
        self.assertEqual(response.state['bat_last_reading'], 3.7)
        self.assertNotEqual(response.state['bat_last_ts'], None)
        self.assertEqual(response.json, {'s': 0})

        # An unknown key shouldn't crash the request
        response = self.webapp_request(unknown='something')
        self.assertEqual(response.json['s'], 0)

        # former created brick is initialized
        response = self.webapp_request(y=['i'])
        self.assertIn('r', response.json)
        self.assertIn(1, response.json['r'])
        self.assertIn(2, response.json['r'])
        self.assertNotIn(3, response.json['r'])
        self.assertIn(4, response.json['r'])

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

        # Test low-bat alarm
        response = self.webapp_request(b=3.7, t=[['sensor1', 24]])
        self.assertNotIn('Charge bat on', response.telegram)
        response = self.webapp_request(b=3.4, t=[['sensor1', 24]])
        self.assertIn('Charge bat on', response.telegram)
        self.assertEqual(response.state['bat_last_reading'], 3.4)
        self.assertEqual(response.state['bat_charging'], False)
        self.assertEqual(response.state['bat_charging_standby'], False)

        # Test usual charging (charging->standby->pull powercord) delay should allways be 60, bat-voltage requested on each statechange
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
        if 'r' in response.json:
            self.assertNotIn(3, response.json['r'])
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
        if 'r' in response.json:
            self.assertNotIn(3, response.json['r'])

        # Test charging interrupt (charging->pull powercord)
        response = self.webapp_request(y=['c'], t=[['sensor1', 24]])
        self.assertEqual(response.state['bat_charging'], True)
        self.assertEqual(response.state['bat_charging_standby'], False)
        response = self.webapp_request(y=[], t=[['sensor1', 24]])
        self.assertEqual(response.state['bat_charging'], False)
        self.assertEqual(response.state['bat_charging_standby'], False)
        self.assertIn('r', response.json)
        self.assertIn(3, response.json['r'])

        # Test periodic request_bat_voltage during charging
        bat_voltage_requests = 0
        next_with_bat = False
        for i in range(0, 20):
            if next_with_bat:
                response = self.webapp_request(y=['c'], t=[['sensor1', 24]], b=3.7)
                next_with_bat = False
            else:
                response = self.webapp_request(y=['c'], t=[['sensor1', 24]])
            if 'r' in response.json and 3 in response.json['r']:
                bat_voltage_requests += 1
                next_with_bat = True
        self.assertEqual(bat_voltage_requests, 2)

        # Test if info-messages send during charging
        response = self.webapp_request(y=['c'], t=[['sensor1', 24]], b=4)
        response = self.webapp_request(y=['c'], t=[['sensor1', 24]], b=4.05)
        response = self.webapp_request(y=['c'], t=[['sensor1', 24]], b=4.1)
        self.assertNotIn('Bat charged over', response.telegram)
        response = self.webapp_request(y=['c'], t=[['sensor1', 24]], b=4.15)
        self.assertIn('Bat charged over', response.telegram)  # Inform admin that bat is now over 4.15 Volts
        response = self.webapp_request(y=['c'], t=[['sensor1', 24]], b=4.15)
        self.assertNotIn('Bat charged over', response.telegram)  # But do not resend the message (spamming protection)
        self.assertNotIn('Charging finished', response.telegram)  # The charging is not finished yet
        response = self.webapp_request(y=['s'], t=[['sensor1', 24]])
        self.assertIn('Charging finished', response.telegram)  # Inform admin that charging has finished
        response = self.webapp_request(y=['c'], t=[['sensor1', 24]], b=4.15)
        response = self.webapp_request(y=[], t=[['sensor1', 24]])
        self.assertNotIn('Charging finished', response.telegram)  # Do not inform Admin that charging has finished if power-cord is pulled

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
        response = self.webapp_request(clear_state=True, v='1.0', f=tempbrick_features)
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
