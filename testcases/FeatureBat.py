from ._wrapper import *
from libfaketime import fake_time
from datetime import datetime, timedelta


@parameterized_class(getVersionParameter('bat'))
class TestFeatureBat(BaseCherryPyTestCase):
    def test_bat_reading_is_stored(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        self.assertEqual(response.state['bat_last_reading'], 0)
        response = self.webapp_request(b=4)
        self.assertEqual(response.state['bat_last_reading'], 4)
        response = self.webapp_request(b=3.5)
        self.assertEqual(response.state['bat_last_reading'], 3.5)

    def test_voltageRequest_on_new_brick(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        self.assertIn('r', response.json)
        self.assertIn(3, response.json['r'])

        # voltage is not delivered, so voltage should be rerequested
        response = self.webapp_request()
        self.assertIn('r', response.json)
        self.assertIn(3, response.json['r'])

        # voltage is now delivered, voltage should not be requested
        response = self.webapp_request(b=4)
        if 'r' in response.json:
            self.assertNotIn(3, response.json['r'])

    def test_voltageRequest_aligned_to_half_past_seven(self):
        # in this case the previous time allready had been aligned to half past 7 (AM or PM) and is requested again around 12 hours later
        dt_now = datetime.now().replace(hour=7, minute=31)

        with fake_time(dt_now - timedelta(hours=12)):
            response = self.webapp_request(clear_state=True, v=self.v)
            self.assertIn('r', response.json)
            self.assertIn(3, response.json['r'])
            response = self.webapp_request(b=4)
            if 'r' in response.json:
                self.assertNotIn(3, response.json['r'])

        for i in reversed(list(range(1, 12))):
            with self.subTest(i=i):
                with fake_time(dt_now - timedelta(hours=i)):
                    response = self.webapp_request()
                    if 'r' in response.json:
                        self.assertNotIn(3, response.json['r'])

        with fake_time(dt_now):
            response = self.webapp_request()
            self.assertIn('r', response.json)
            self.assertIn(3, response.json['r'])

    def test_voltageRequest_aligne_to_half_past_seven_expand(self):
        # in the time between hour % 12  between 1 and 6 the 12 hour timespan is expanded by 30 minutes
        dt_now = datetime.now().replace(hour=4)

        with fake_time(dt_now - timedelta(hours=12)):
            response = self.webapp_request(clear_state=True, v=self.v)
            self.assertIn('r', response.json)
            self.assertIn(3, response.json['r'])
            response = self.webapp_request(b=4)
            if 'r' in response.json:
                self.assertNotIn(3, response.json['r'])

        for i in reversed(list(range(0, 12))):
            with self.subTest(i=i):
                with fake_time(dt_now - timedelta(hours=i)):
                    response = self.webapp_request()
                    if 'r' in response.json:
                        self.assertNotIn(3, response.json['r'])

        with fake_time(dt_now + timedelta(hours=1)):
            response = self.webapp_request()
            self.assertIn('r', response.json)
            self.assertIn(3, response.json['r'])

    def test_voltageRequest_aligne_to_half_past_seven_shorten(self):
        # in the time between hour % 12  between 8 and 12 the 12 hour timespan is shortened by 30 minutes
        dt_now = datetime.now().replace(hour=21)

        with fake_time(dt_now - timedelta(hours=12)):
            response = self.webapp_request(clear_state=True, v=self.v)
            self.assertIn('r', response.json)
            self.assertIn(3, response.json['r'])
            response = self.webapp_request(b=4)
            if 'r' in response.json:
                self.assertNotIn(3, response.json['r'])

        for i in reversed(list(range(1, 12))):
            with self.subTest(i=i):
                with fake_time(dt_now - timedelta(hours=i)):
                    response = self.webapp_request()
                    if 'r' in response.json:
                        self.assertNotIn(3, response.json['r'])

        with fake_time(dt_now):
            response = self.webapp_request()
            self.assertIn('r', response.json)
            self.assertIn(3, response.json['r'])

    def test_voltageRequest_after_init(self):
        response = self.webapp_request(clear_state=True, v=self.v, b=3.5)

        # voltage allready delivered, should not be requested for now
        if 'r' in response.json:
            self.assertNotIn(3, response.json['r'])

        # init is send over (e.g. because bat was changed) the voltage should now be requested
        response = self.webapp_request(y=['i'])
        self.assertIn('r', response.json)
        self.assertIn(3, response.json['r'])

        # but not rerequested if not send over
        response = self.webapp_request()
        if 'r' in response.json:
            self.assertNotIn(3, response.json['r'])

    def test_bat_charging_is_stored(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        self.assertFalse(response.state['bat_charging'])
        response = self.webapp_request(y=['c'])
        self.assertTrue(response.state['bat_charging'])
        response = self.webapp_request(y=[])
        self.assertFalse(response.state['bat_charging'])
        response = self.webapp_request(y=['c'])
        self.assertTrue(response.state['bat_charging'])
        response = self.webapp_request()
        self.assertFalse(response.state['bat_charging'])

    def test_bat_charging_standby_is_stored(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        self.assertFalse(response.state['bat_charging_standby'])
        response = self.webapp_request(y=['s'])
        self.assertTrue(response.state['bat_charging_standby'])
        response = self.webapp_request(y=[])
        self.assertFalse(response.state['bat_charging_standby'])
        response = self.webapp_request(y=['s'])
        self.assertTrue(response.state['bat_charging_standby'])
        response = self.webapp_request()
        self.assertFalse(response.state['bat_charging_standby'])

    def test_set_solar_charging_api(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        self.assertFalse(response.state['bat_solar_charging'])
        response = self.webapp_request(path='/admin', command='set', brick='localhost', key='bat_solar_charging', value='true')
        self.assertEqual(response.json['s'], 7)  # invalid value, needs to be bool
        response = self.webapp_request(path='/admin', command='set', brick='localhost', key='bat_solar_charging', value=True)
        self.assertTrue(response.state['bat_solar_charging'])

    def test_periodic_voltageRequest_on_charging(self):
        response = self.webapp_request(clear_state=True, v=self.v, b=4)
        if 'r' in response.json:
            self.assertNotIn(3, response.json['r'])
        self.assertEqual(response.state['bat_periodic_voltage_request'], 10)

        rounds = [(1, False, 9), (2, False, 8), (3, False, 7), (4, False, 6), (5, False, 5),
                  (6, False, 4), (7, False, 3), (8, False, 2), (9, False, 1), (10, True, 10),
                  (11, False, 9), (12, False, 8), (13, False, 7), (14, False, 6), (15, False, 5),
                  (16, False, 4), (17, False, 3), (18, False, 2), (19, False, 1), (20, True, 10)]
        for rnd, requestVoltage, periodic in rounds:
            with self.subTest(rnd=rnd, requestVoltage=requestVoltage, periodic=periodic):
                response = self.webapp_request(y=['c'])
                self.assertEqual(response.state['bat_periodic_voltage_request'], periodic)
                if requestVoltage:
                    self.assertIn(3, response.json['r'])

    def test_no_periodic_voltageRequest_on_charging_standby(self):
        response = self.webapp_request(clear_state=True, v=self.v, b=4)
        if 'r' in response.json:
            self.assertNotIn(3, response.json['r'])
        self.assertEqual(response.state['bat_periodic_voltage_request'], 10)

        for i in range(0, 21):
            with self.subTest(rnd=i):
                response = self.webapp_request(y=['s'])
                if 'r' in response.json:
                    self.assertNotIn(3, response.json['r'])
                self.assertEqual(response.state['bat_periodic_voltage_request'], 10)

    def test_no_periodic_voltageRequest_on_solar_charging(self):
        response = self.webapp_request(clear_state=True, v=self.v, b=4)
        response = self.webapp_request(path='/admin', command='set', brick='localhost', key='bat_solar_charging', value=True)
        if 'r' in response.json:
            self.assertNotIn(3, response.json['r'])
        self.assertEqual(response.state['bat_periodic_voltage_request'], 10)

        for i in range(0, 21):
            with self.subTest(rnd=i):
                response = self.webapp_request(y=['c'])
                if 'r' in response.json:
                    self.assertNotIn(3, response.json['r'])
                self.assertEqual(response.state['bat_periodic_voltage_request'], 10)

    def test_bat_runtime_prediction_is_calculated(self):
        dt_now = datetime.now()

        with fake_time(dt_now - timedelta(hours=24)):
            response = self.webapp_request(clear_state=True, v=self.v, b=4)
            self.assertIsNone(response.state['bat_runtime_prediction'])

        with fake_time(dt_now - timedelta(hours=12)):
            response = self.webapp_request(b=3.9)
            self.assertIsNotNone(response.state['bat_runtime_prediction'])
            brp = response.state['bat_runtime_prediction']

        with fake_time(dt_now):
            response = self.webapp_request(b=3.7)
            self.assertIsNotNone(response.state['bat_runtime_prediction'])
            self.assertNotEqual(response.state['bat_runtime_prediction'], brp)

    def test_bat_runtime_prediction_is_not_calculated_during_charging(self):
        dt_now = datetime.now()

        with fake_time(dt_now - timedelta(hours=24)):
            response = self.webapp_request(clear_state=True, v=self.v, b=4)
            self.assertIsNone(response.state['bat_runtime_prediction'])

        with fake_time(dt_now - timedelta(hours=12)):
            response = self.webapp_request(b=3.9, y=['c'])
            self.assertIsNone(response.state['bat_runtime_prediction'])

    def test_bat_runtime_prediction_is_not_calculated_during_charging_standby(self):
        dt_now = datetime.now()

        with fake_time(dt_now - timedelta(hours=24)):
            response = self.webapp_request(clear_state=True, v=self.v, b=4)
            self.assertIsNone(response.state['bat_runtime_prediction'])

        with fake_time(dt_now - timedelta(hours=12)):
            response = self.webapp_request(b=3.9, y=['s'])
            self.assertIsNone(response.state['bat_runtime_prediction'])

    def test_bat_runtime_prediction_is_calculated_during_solar_charging(self):
        dt_now = datetime.now()

        with fake_time(dt_now - timedelta(hours=24)):
            response = self.webapp_request(clear_state=True, v=self.v, b=4)
            response = self.webapp_request(path='/admin', command='set', brick='localhost', key='bat_solar_charging', value=True)
            self.assertIsNone(response.state['bat_runtime_prediction'])

        with fake_time(dt_now - timedelta(hours=12)):
            response = self.webapp_request(b=3.9, y=['c'])
            self.assertIsNotNone(response.state['bat_runtime_prediction'])

    def test_bat_runtime_prediction_is_calculated_during_solar_charging_standby(self):
        dt_now = datetime.now()

        with fake_time(dt_now - timedelta(hours=24)):
            response = self.webapp_request(clear_state=True, v=self.v, b=4)
            response = self.webapp_request(path='/admin', command='set', brick='localhost', key='bat_solar_charging', value=True)
            self.assertIsNone(response.state['bat_runtime_prediction'])

        with fake_time(dt_now - timedelta(hours=12)):
            response = self.webapp_request(b=3.9, y=['s'])
            self.assertIsNotNone(response.state['bat_runtime_prediction'])

    def test_telegram_messages_are_send_without_desc(self):
        response = self.webapp_request(clear_state=True, v=self.v, b=3.35)
        self.assertIn('Charge bat on localhost it reads 3.35 Volts', response.telegram)

        response = self.webapp_request(y=['c'], b=4.13)
        self.assertNotIn('Bat charged over 4.15Volts', response.telegram)
        response = self.webapp_request(y=['c'], b=4.14)
        self.assertNotIn('Bat charged over 4.15Volts', response.telegram)
        response = self.webapp_request(y=['c'], b=4.15)
        self.assertIn('Bat charged over 4.15Volts on localhost', response.telegram)

        response = self.webapp_request(y=['s'])
        self.assertIn('Charging finished on localhost', response.telegram)

    def test_telegram_messages_are_send_with_desc(self):
        response = self.webapp_request(clear_state=True, v=self.v, b=3.35)
        self.webapp_request(path='/admin', command='set', brick='localhost', key='desc', value='somebrick')
        response = self.webapp_request(b=3.35)
        self.assertIn('Charge bat on somebrick it reads 3.35 Volts', response.telegram)

        response = self.webapp_request(y=['c'], b=4.13)
        self.assertNotIn('Bat charged over 4.15Volts', response.telegram)
        response = self.webapp_request(y=['c'], b=4.14)
        self.assertNotIn('Bat charged over 4.15Volts', response.telegram)
        response = self.webapp_request(y=['c'], b=4.15)
        self.assertIn('Bat charged over 4.15Volts on somebrick', response.telegram)

        response = self.webapp_request(y=['s'])
        self.assertIn('Charging finished on somebrick', response.telegram)

    def test_admin_override_voltage_request(self):
        response = self.webapp_request(clear_state=True, v=self.v, b=3.6)
        if 'r' in response.json:
            self.assertNotIn(3, response.json['r'])

        self.webapp_request(path='/admin', command='set', brick='localhost', key='bat_voltage', value=True)
        response = self.webapp_request()
        self.assertIn('r', response.json)
        self.assertIn(3, response.json['r'])

    def test_mqtt_messages_are_send(self):
        dt_now = datetime.now()

        with fake_time(dt_now - timedelta(hours=24)):
            response = self.webapp_request(clear_state=True, mqtt_test=True, v=self.v, b=3.8)
            self.assertIn('brick/localhost/bat/voltage 3.8', response.mqtt)

        response = self.webapp_request(mqtt_test=True, b=3.7)
        self.assertIn('brick/localhost/bat/voltage 3.7', response.mqtt)
        self.assertIn('brick/localhost/bat/prediction', response.mqtt)

        response = self.webapp_request(mqtt_test=True)
        self.assertNotIn('brick/localhost/bat/', response.mqtt)

        response = self.webapp_request(mqtt_test=True, y=['c'])
        self.assertIn('brick/localhost/bat/charging 1', response.mqtt)

        response = self.webapp_request(mqtt_test=True, y=['s'])
        self.assertIn('brick/localhost/bat/charging 2', response.mqtt)

        response = self.webapp_request(mqtt_test=True)
        self.assertIn('brick/localhost/bat/charging 0', response.mqtt)

        response = self.webapp_request(mqtt_test=True)
        self.assertNotIn('brick/localhost/bat/', response.mqtt)


@parameterized_class(getVersionParameter('bat', specificVersion=[['bat', 1.01]], minVersion={'bat': 1.01}))
class TestFeatureBatV101(BaseCherryPyTestCase):
    def test_version_specific_attributes(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        self.assertIn('bat_adc5V', response.state)
        self.assertIsNone(response.state['bat_adc5V'])

    def test_delivered_adc5V_is_stored(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        self.assertIsNone(response.state['bat_adc5V'])

        response = self.webapp_request(a=800)
        self.assertEqual(response.state['bat_adc5V'], 800)

        response = self.webapp_request(a=900)
        self.assertEqual(response.state['bat_adc5V'], 900)

    def test_adc5V_attribute_is_reset_on_init(self):
        response = self.webapp_request(clear_state=True, v=self.v, a=800)
        self.assertEqual(response.state['bat_adc5V'], 800)

        response = self.webapp_request(y=['i'])
        self.assertIsNone(response.state['bat_adc5V'])

    def test_adc5V_value_is_send_as_feedback(self):
        response = self.webapp_request(clear_state=True, v=self.v, b=4.27, a=800)
        self.assertNotIn('a', response.json)

        response = self.webapp_request(path='/admin', brick='localhost', command='set', key='bat_adc5V', value=820)

        response = self.webapp_request()
        self.assertIn('a', response.json)
        self.assertEqual(response.json['a'], 820)

    def test_adc5V_is_requested(self):
        # if bat_adc5V is None
        response = self.webapp_request(clear_state=True, v=self.v)
        self.assertIsNone(response.state['bat_adc5V'])
        self.assertIn('r', response.json)
        self.assertIn(10, response.json['r'])

        # if brick send an init
        response = self.webapp_request(a=800)
        if 'r' in response.json:
            self.assertNotIn(10, response.json['r'])

        response = self.webapp_request(y=['i'])
        self.assertIn('r', response.json)
        self.assertIn(10, response.json['r'])

    def test_bat_init_ts_is_reset_on_adv5V_set(self):
        response = self.webapp_request(clear_state=True, v=self.v, b=4.27, a=800)
        self.assertEqual(response.state['bat_init_voltage'], 4.27)
        self.assertIsNotNone(response.state['bat_init_ts'])

        response = self.webapp_request(path='/admin', brick='localhost', command='set', key='bat_adc5V', value=820)

        self.assertIsNone(response.state['bat_init_voltage'])
        self.assertIsNone(response.state['bat_init_ts'])

        # this results in requesting the bat_voltage
        response = self.webapp_request()
        self.assertIn('r', response.json)
        self.assertIn(3, response.json['r'])

    def test_admin_interface_set_adc5V_values(self):
        response = self.webapp_request(clear_state=True)

        response = self.webapp_request(path='/admin', brick='localhost', command='set', key='bat_adc5V', value=820)  # bat not in brick-features
        self.assertEqual(response.json['s'], 36)

        response = self.webapp_request(v=self.v, b=4.27, a=800)

        response = self.webapp_request(path='/admin', brick='localhost', command='set', key='bat_adc5V', value=820)
        self.assertEqual(response.json['s'], 0)

        response = self.webapp_request(path='/admin', brick='localhost', command='set', key='bat_adc5V', value=-1)
        self.assertEqual(response.json['s'], 7)

        response = self.webapp_request(path='/admin', brick='localhost', command='set', key='bat_adc5V', value=0)
        self.assertEqual(response.json['s'], 0)

        response = self.webapp_request(path='/admin', brick='localhost', command='set', key='bat_adc5V', value=1023)
        self.assertEqual(response.json['s'], 0)

        response = self.webapp_request(path='/admin', brick='localhost', command='set', key='bat_adc5V', value=1024)
        self.assertEqual(response.json['s'], 7)


@parameterized_class(getVersionParameter('bat', specificVersion=[['bat', 3]], minVersion={'bat': 3}))
class TestFeatureBatV3(BaseCherryPyTestCase):
    def test_wall_powered_is_stored(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        self.assertFalse(response.state['bat_wall_powered'])

        response = self.webapp_request(y=['w'])
        self.assertTrue(response.state['bat_wall_powered'])

        response = self.webapp_request()
        self.assertFalse(response.state['bat_wall_powered'])
