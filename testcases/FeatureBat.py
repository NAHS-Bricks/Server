from ._wrapper import *
from freezegun import freeze_time
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

    def test_voltageRequest_after_12_hours(self):
        dt_now = datetime.now()

        with freeze_time(dt_now - timedelta(hours=13)):
            response = self.webapp_request(clear_state=True, v=self.v)
            self.assertIn('r', response.json)
            self.assertIn(3, response.json['r'])
            response = self.webapp_request(b=4)
            if 'r' in response.json:
                self.assertNotIn(3, response.json['r'])

        for i in reversed(list(range(1, 13))):
            with self.subTest(i=i):
                with freeze_time(dt_now - timedelta(hours=i)):
                    response = self.webapp_request()
                    if 'r' in response.json:
                        self.assertNotIn(3, response.json['r'])

        with freeze_time(dt_now):
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
                if 'r' in response.json:
                    self.assertNotIn(3, response.json['r'])
                self.assertEqual(response.state['bat_periodic_voltage_request'], 10)

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
