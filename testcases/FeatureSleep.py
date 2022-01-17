from ._wrapper import *


@parameterized_class(getVersionParameter('sleep', '*'))
class TestFeatureSleep(BaseCherryPyTestCase):
    def test_inactiv_by_its_own(self):
        response = self.webapp_request(clear_state=True, v=self.v, d=60, m='1')  # m for getting rid of other features requests
        self.assertNotIn('d', response.json)
        self.assertIn('sleep_increase_wait', response.state)
        self.assertEqual(response.state['sleep_increase_wait'], 2)

        response = self.webapp_request()
        self.assertNotIn('d', response.json)
        self.assertEqual(response.state['sleep_increase_wait'], 1)

        for i in range(0, 20):
            with self.subTest(i=i):
                response = self.webapp_request()
                self.assertNotIn('d', response.json)
                self.assertEqual(response.state['sleep_increase_wait'], 0)

    def test_admin_override_delay(self):
        response = self.webapp_request(clear_state=True, v=self.v, d=60, m='1')  # m for getting rid of other features requests
        self.assertNotIn('d', response.json)
        self.assertIn('sleep_increase_wait', response.state)
        self.assertEqual(response.state['sleep_increase_wait'], 2)

        self.webapp_request(path='/admin', command="set", brick='localhost', key='delay', value=30)
        response = self.webapp_request()
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 30)
        self.assertIn('sleep_increase_wait', response.state)
        self.assertEqual(response.state['sleep_increase_wait'], 3)


@parameterized_class(getVersionParameter('sleep', '*', minVersion={'all': 1.02}))
class TestFeatureSleep_withAllV102(BaseCherryPyTestCase):
    def test_admin_override_delay_with_delay_overwrite(self):
        response = self.webapp_request(clear_state=True, v=self.v, d=60, y=['d'])
        self.assertNotIn('d', response.json)

        self.webapp_request(path='/admin', command="set", brick='localhost', key='delay', value=30)
        response = self.webapp_request(y=['d'])
        self.assertNotIn('d', response.json)
        self.assertEqual(response.state['delay'], 60)


@parameterized_class(getVersionParameter('sleep', '*', minVersion={'all': 1.02, 'sleep': 1.01}))
class TestFeatureSleepV101(BaseCherryPyTestCase):
    def test_sleep_disabled(self):
        response = self.webapp_request(clear_state=True, v=self.v, d=60, m='1')  # m for getting rid of other features requests
        self.assertFalse(response.state['sleep_disabled'])
        self.assertFalse(response.state['sleep_set_disabled'])

        # setting sleep_disabled via API
        response = self.webapp_request(path='/admin', command="set", brick='localhost', key='sleep_disabled', value=True)
        self.assertEqual(response.json['s'], 0)
        self.assertFalse(response.state['sleep_disabled'])
        self.assertTrue(response.state['sleep_set_disabled'])

        # new value should now gets transmitted and delay should be set to 10
        response = self.webapp_request()
        self.assertEqual(response.json['d'], 10)
        self.assertTrue(response.json['q'])

        # sleep_disabled now True on brick, dont resend q but reset delay to default
        response = self.webapp_request(y=['q'])
        self.assertEqual(response.json['d'], 60)
        self.assertNotIn('q', response.json)
        self.assertTrue(response.state['sleep_disabled'])
        self.assertTrue(response.state['sleep_set_disabled'])

        # set it back to False
        response = self.webapp_request(path='/admin', command="set", brick='localhost', key='sleep_disabled', value=False)
        self.assertTrue(response.state['sleep_disabled'])
        self.assertFalse(response.state['sleep_set_disabled'])
        response = self.webapp_request(y=['q'])
        self.assertEqual(response.json['d'], 10)
        self.assertFalse(response.json['q'])

        # check everything as expected
        response = self.webapp_request()
        self.assertEqual(response.json['d'], 60)
        self.assertNotIn('q', response.json)
        self.assertFalse(response.state['sleep_disabled'])
        self.assertFalse(response.state['sleep_set_disabled'])


@parameterized_class(getVersionParameter(['sleep', 'bat']))
class TestFeatureSleepWithBat(BaseCherryPyTestCase):
    def test_charging(self):
        response = self.webapp_request(clear_state=True, v=self.v, d=60, b=4, p=11, y=['c'], s=1, m='1')  # m, p and s for getting rid of other features requests
        self.assertEqual(response.state['delay'], 60)
        self.assertIn('sleep_increase_wait', response.state)
        self.assertEqual(response.state['sleep_increase_wait'], 3)

        for i in range(0, 20):
            with self.subTest(i=i):
                response = self.webapp_request(b=4, y=['c'])
                if i % 10 == 8:
                    self.assertIn('d', response.json)
                    self.assertEqual(response.json['d'], 10)  # every 10 times the battery voltage is requested, so delay is set to 10 for these ones
                elif i % 10 == 9:
                    self.assertIn('d', response.json)
                    self.assertEqual(response.json['d'], 60)  # after voltage was requested, set delay back to 60
                else:
                    self.assertEqual(response.state['delay'], 60)
                self.assertIn('sleep_increase_wait', response.state)
                self.assertEqual(response.state['sleep_increase_wait'], 3)

    def test_charging_standby(self):
        response = self.webapp_request(clear_state=True, v=self.v, d=60, b=4.2, p=11, y=['s'], s=1, m='1')  # m, p and s for getting rid of other features requests
        self.assertEqual(response.state['delay'], 60)
        self.assertIn('sleep_increase_wait', response.state)
        self.assertEqual(response.state['sleep_increase_wait'], 3)

        for i in range(0, 20):
            with self.subTest(i=i):
                response = self.webapp_request(y=['s'])
                self.assertEqual(response.state['delay'], 60)
                self.assertIn('sleep_increase_wait', response.state)
                self.assertEqual(response.state['sleep_increase_wait'], 3)

    def test_admin_override_delay_charging(self):
        response = self.webapp_request(clear_state=True, v=self.v, d=60, b=4.2, p=11, y=['c'], s=1, m='1')  # m, p and s for getting rid of other features requests
        self.assertEqual(response.state['delay'], 60)
        self.assertIn('sleep_increase_wait', response.state)
        self.assertEqual(response.state['sleep_increase_wait'], 3)

        self.webapp_request(path='/admin', command="set", brick='localhost', key='delay', value=30)
        response = self.webapp_request(y=['c'])
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 30)
        self.assertIn('sleep_increase_wait', response.state)
        self.assertEqual(response.state['sleep_increase_wait'], 3)

    def test_admin_override_delay_standby(self):
        response = self.webapp_request(clear_state=True, v=self.v, d=60, b=4.2, p=11, y=['s'], s=1, m='1')  # m, p and s for getting rid of other features requests
        self.assertEqual(response.state['delay'], 60)
        self.assertIn('sleep_increase_wait', response.state)
        self.assertEqual(response.state['sleep_increase_wait'], 3)

        self.webapp_request(path='/admin', command="set", brick='localhost', key='delay', value=30)
        response = self.webapp_request(y=['s'])
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 30)
        self.assertIn('sleep_increase_wait', response.state)
        self.assertEqual(response.state['sleep_increase_wait'], 3)


@parameterized_class(getVersionParameter(['sleep', 'bat'], minVersion={'all': 1.02}))
class TestFeatureSleepWithBatWithAllV102(BaseCherryPyTestCase):
    def test_admin_override_delay_charging_with_delay_overwrite(self):
        response = self.webapp_request(clear_state=True, v=self.v, b=4.2, p=11, d=120, y=['c', 'd'], s=1, m='1')  # m, p and s for getting rid of other features requests
        self.assertNotIn('d', response.json)
        self.assertEqual(response.state['delay'], 120)

        self.webapp_request(path='/admin', command="set", brick='localhost', key='delay', value=30)
        response = self.webapp_request(y=['c', 'd'])
        self.assertNotIn('d', response.json)
        self.assertEqual(response.state['delay'], 120)


@parameterized_class(getVersionParameter(['sleep', 'bat'], ['temp', 'humid', 'latch', 'signal']))
class TestFeatureSleepWithBatSolarCharging(BaseCherryPyTestCase):
    def test_solar_charging(self):  # expected to not effect delay
        response = self.webapp_request(clear_state=True, v=self.v, d=60, b=4, y=['c'], m='1')  # m for getting rid of other features requests
        response = self.webapp_request(path='/admin', command='set', brick='localhost', key='bat_solar_charging', value=True)
        response = self.webapp_request(b=4, y=['c'])
        self.assertNotIn('d', response.json)
        self.assertIn('sleep_increase_wait', response.state)
        self.assertEqual(response.state['sleep_increase_wait'], 2)

        response = self.webapp_request(b=4, y=['c'])
        self.assertNotIn('d', response.json)
        self.assertEqual(response.state['sleep_increase_wait'], 1)

        for i in range(0, 20):
            with self.subTest(i=i):
                response = self.webapp_request(b=4, y=['c'])
                self.assertNotIn('d', response.json)
                self.assertEqual(response.state['sleep_increase_wait'], 0)

    def test_solar_charging_standby(self):  # expected to not effect delay
        response = self.webapp_request(clear_state=True, v=self.v, d=60, b=4, y=['s'], m='1')  # m for getting rid of other features requests
        response = self.webapp_request(path='/admin', command='set', brick='localhost', key='bat_solar_charging', value=True)
        response = self.webapp_request(b=4, y=['s'])
        self.assertNotIn('d', response.json)
        self.assertIn('sleep_increase_wait', response.state)
        self.assertEqual(response.state['sleep_increase_wait'], 2)

        response = self.webapp_request(b=4, y=['s'])
        self.assertNotIn('d', response.json)
        self.assertEqual(response.state['sleep_increase_wait'], 1)

        for i in range(0, 20):
            with self.subTest(i=i):
                response = self.webapp_request(b=4, y=['s'])
                self.assertNotIn('d', response.json)
                self.assertEqual(response.state['sleep_increase_wait'], 0)


@parameterized_class(getVersionParameter(['sleep', 'temp'], 'signal'))
class TestFeatureSleepWithTemp(BaseCherryPyTestCase):
    def test_delay_increase_on_stable_temp(self):
        response = self.webapp_request(clear_state=True, v=self.v, t=[['s1', 25]], c=[['s1', 0]], d=60, p=11, b=4, s=1, m='1')  # m, b and s for getting rid of other features requests
        self.assertIn('sleep_increase_wait', response.state)
        self.assertEqual(response.state['sleep_increase_wait'], 2)

        rounds = [(1, None, 3), (2, None, 2), (3, None, 1),
                  (4, 120, 3), (5, None, 2), (6, None, 1),
                  (7, 180, 3), (8, None, 2), (9, None, 1),
                  (10, 240, 3), (11, None, 2), (12, None, 1),
                  (13, 300, 3), (14, None, 2), (15, None, 1),
                  (16, None, 0), (17, None, 0), (18, None, 0)]

        for rnd, delay, wait in rounds:
            with self.subTest(rnd=rnd, delay=delay, wait=wait):
                response = self.webapp_request(t=[['s1', 24]])
                if delay is None:
                    self.assertNotIn('d', response.json)
                else:
                    self.assertIn('d', response.json)
                    self.assertEqual(response.json['d'], delay)
                self.assertIn('sleep_increase_wait', response.state)
                self.assertEqual(response.state['sleep_increase_wait'], wait)

    def test_no_delay_decrease_on_positive_point25_change(self):
        response = self.webapp_request(clear_state=True, v=self.v, t=[['s1', 25]], c=[['s1', 0]], d=60, p=11, b=4, s=1, m='1')  # m, b and s for getting rid of other features requests
        for i in range(0, 4):
            response = self.webapp_request(t=[['s1', 24]])
        self.assertEqual(response.state['delay'], 120)
        response = self.webapp_request(t=[['s1', 24.25]])
        self.assertNotIn('d', response.json)
        self.assertEqual(response.state['delay'], 120)

        response = self.webapp_request(clear_state=True, v=self.v, t=[['s1', 25]], c=[['s1', 0]], d=60, p=11, b=4, s=1, m='1')  # m, b and s for getting rid of other features requests
        for i in range(0, 7):
            response = self.webapp_request(t=[['s1', 24]])
        self.assertEqual(response.state['delay'], 180)
        response = self.webapp_request(t=[['s1', 24.25]])
        self.assertNotIn('d', response.json)
        self.assertEqual(response.state['delay'], 180)

    def test_no_delay_decrease_on_negative_point25_change(self):
        response = self.webapp_request(clear_state=True, v=self.v, t=[['s1', 25]], c=[['s1', 0]], d=60, p=11, b=4, s=1, m='1')  # m, b and s for getting rid of other features requests
        for i in range(0, 4):
            response = self.webapp_request(t=[['s1', 24]])
        self.assertEqual(response.state['delay'], 120)
        response = self.webapp_request(t=[['s1', 23.75]])
        self.assertNotIn('d', response.json)
        self.assertEqual(response.state['delay'], 120)

        response = self.webapp_request(clear_state=True, v=self.v, t=[['s1', 25]], c=[['s1', 0]], d=60, p=11, b=4, s=1, m='1')  # m, b and s for getting rid of other features requests
        for i in range(0, 7):
            response = self.webapp_request(t=[['s1', 24]])
        self.assertEqual(response.state['delay'], 180)
        response = self.webapp_request(t=[['s1', 23.75]])
        self.assertNotIn('d', response.json)
        self.assertEqual(response.state['delay'], 180)

    def test_delay_decrease_on_positive_point26_change(self):
        response = self.webapp_request(clear_state=True, v=self.v, t=[['s1', 25]], c=[['s1', 0]], d=60, p=11, b=4, s=1, m='1')  # m, b and s for getting rid of other features requests
        for i in range(0, 4):
            response = self.webapp_request(t=[['s1', 24]])
        self.assertEqual(response.state['delay'], 120)
        response = self.webapp_request(t=[['s1', 24.26]])
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 60)
        self.assertEqual(response.state['delay'], 60)

        response = self.webapp_request(clear_state=True, v=self.v, t=[['s1', 25]], c=[['s1', 0]], d=60, p=11, b=4, s=1, m='1')  # m, b and s for getting rid of other features requests
        for i in range(0, 7):
            response = self.webapp_request(t=[['s1', 24]])
        self.assertEqual(response.state['delay'], 180)
        response = self.webapp_request(t=[['s1', 24.26]])
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 60)
        self.assertEqual(response.state['delay'], 60)

    def test_delay_decrease_on_negative_point26_change(self):
        response = self.webapp_request(clear_state=True, v=self.v, t=[['s1', 25]], c=[['s1', 0]], d=60, p=11, b=4, s=1, m='1')  # m, b and s for getting rid of other features requests
        for i in range(0, 4):
            response = self.webapp_request(t=[['s1', 24]])
        self.assertEqual(response.state['delay'], 120)
        response = self.webapp_request(t=[['s1', 23.74]])
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 60)
        self.assertEqual(response.state['delay'], 60)

        response = self.webapp_request(clear_state=True, v=self.v, t=[['s1', 25]], c=[['s1', 0]], d=60, p=11, b=4, s=1, m='1')  # m, b and s for getting rid of other features requests
        for i in range(0, 7):
            response = self.webapp_request(t=[['s1', 24]])
        self.assertEqual(response.state['delay'], 180)
        response = self.webapp_request(t=[['s1', 23.74]])
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 60)
        self.assertEqual(response.state['delay'], 60)

    def test_admin_override_delay(self):
        response = self.webapp_request(clear_state=True, v=self.v, t=[['s1', 25]], c=[['s1', 0]], d=60, p=11, b=4, s=1, m='1')  # m, b and s for getting rid of other features requests
        for i in range(0, 4):
            response = self.webapp_request(t=[['s1', 24]])
        self.assertEqual(response.state['delay'], 120)

        self.webapp_request(path='/admin', command="set", brick='localhost', key='delay', value=30)
        response = self.webapp_request(t=[['s1', 24]])
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 30)
        self.assertIn('sleep_increase_wait', response.state)
        self.assertEqual(response.state['sleep_increase_wait'], 3)


@parameterized_class(getVersionParameter(['sleep', 'humid'], 'signal'))
class TestFeatureSleepWithHumid(BaseCherryPyTestCase):
    def test_delay_increase_on_stable_humidity(self):
        response = self.webapp_request(clear_state=True, v=self.v, h=[['h1', 51]], k=[['h1', 0]], d=60, p=11, b=4, s=1, m='1')  # m, p, b and s for getting rid of other features requests
        self.assertIn('sleep_increase_wait', response.state)
        self.assertEqual(response.state['sleep_increase_wait'], 2)

        rounds = [(1, None, 3), (2, None, 2), (3, None, 1),
                  (4, 120, 3), (5, None, 2), (6, None, 1),
                  (7, 180, 3), (8, None, 2), (9, None, 1),
                  (10, 240, 3), (11, None, 2), (12, None, 1),
                  (13, 300, 3), (14, None, 2), (15, None, 1),
                  (16, None, 0), (17, None, 0), (18, None, 0)]

        for rnd, delay, wait in rounds:
            with self.subTest(rnd=rnd, delay=delay, wait=wait):
                response = self.webapp_request(h=[['h1', 50]])
                if delay is None:
                    self.assertNotIn('d', response.json)
                else:
                    self.assertIn('d', response.json)
                    self.assertEqual(response.json['d'], delay)
                self.assertIn('sleep_increase_wait', response.state)
                self.assertEqual(response.state['sleep_increase_wait'], wait)

    def test_no_delay_decrease_on_positive_point25_change(self):
        response = self.webapp_request(clear_state=True, v=self.v, h=[['h1', 51]], k=[['h1', 0]], d=60, p=11, b=4, s=1, m='1')  # m, p, b and s for getting rid of other features requests
        for i in range(0, 4):
            response = self.webapp_request(h=[['h1', 50]])
        self.assertEqual(response.state['delay'], 120)
        response = self.webapp_request(h=[['h1', 50.25]])
        self.assertNotIn('d', response.json)
        self.assertEqual(response.state['delay'], 120)

        response = self.webapp_request(clear_state=True, v=self.v, h=[['h1', 51]], k=[['h1', 0]], d=60, p=11, b=4, s=1, m='1')  # m, p, b and s for getting rid of other features requests
        for i in range(0, 7):
            response = self.webapp_request(h=[['h1', 50]])
        self.assertEqual(response.state['delay'], 180)
        response = self.webapp_request(h=[['h1', 50.25]])
        self.assertNotIn('d', response.json)
        self.assertEqual(response.state['delay'], 180)

    def test_no_delay_decrease_on_negative_point25_change(self):
        response = self.webapp_request(clear_state=True, v=self.v, h=[['h1', 51]], k=[['h1', 0]], d=60, p=11, b=4, s=1, m='1')  # m, p, b and s for getting rid of other features requests
        for i in range(0, 4):
            response = self.webapp_request(h=[['h1', 50]])
        self.assertEqual(response.state['delay'], 120)
        response = self.webapp_request(h=[['h1', 49.75]])
        self.assertNotIn('d', response.json)
        self.assertEqual(response.state['delay'], 120)

        response = self.webapp_request(clear_state=True, v=self.v, h=[['h1', 51]], k=[['h1', 0]], d=60, p=11, b=4, s=1, m='1')  # m, p, b and s for getting rid of other features requests
        for i in range(0, 7):
            response = self.webapp_request(h=[['h1', 50]])
        self.assertEqual(response.state['delay'], 180)
        response = self.webapp_request(h=[['h1', 49.75]])
        self.assertNotIn('d', response.json)
        self.assertEqual(response.state['delay'], 180)

    def test_delay_decrease_on_positive_point26_change(self):
        response = self.webapp_request(clear_state=True, v=self.v, h=[['h1', 51]], k=[['h1', 0]], d=60, p=11, b=4, s=1, m='1')  # m, p, b and s for getting rid of other features requests
        for i in range(0, 4):
            response = self.webapp_request(h=[['h1', 50]])
        self.assertEqual(response.state['delay'], 120)
        response = self.webapp_request(h=[['h1', 50.26]])
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 60)
        self.assertEqual(response.state['delay'], 60)

        response = self.webapp_request(clear_state=True, v=self.v, h=[['h1', 51]], k=[['h1', 0]], d=60, p=11, b=4, s=1, m='1')  # m, p, b and s for getting rid of other features requests
        for i in range(0, 7):
            response = self.webapp_request(h=[['h1', 50]])
        self.assertEqual(response.state['delay'], 180)
        response = self.webapp_request(h=[['h1', 50.26]])
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 60)
        self.assertEqual(response.state['delay'], 60)

    def test_delay_decrease_on_negative_point26_change(self):
        response = self.webapp_request(clear_state=True, v=self.v, h=[['h1', 51]], k=[['h1', 0]], d=60, p=11, b=4, s=1, m='1')  # m, p, b and s for getting rid of other features requests
        for i in range(0, 4):
            response = self.webapp_request(h=[['h1', 50]])
        self.assertEqual(response.state['delay'], 120)
        response = self.webapp_request(h=[['h1', 49.74]])
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 60)
        self.assertEqual(response.state['delay'], 60)

        response = self.webapp_request(clear_state=True, v=self.v, h=[['h1', 51]], k=[['h1', 0]], d=60, p=11, b=4, s=1, m='1')  # m, p, b and s for getting rid of other features requests
        for i in range(0, 7):
            response = self.webapp_request(h=[['h1', 50]])
        self.assertEqual(response.state['delay'], 180)
        response = self.webapp_request(h=[['h1', 49.74]])
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 60)
        self.assertEqual(response.state['delay'], 60)

    def test_admin_override_delay(self):
        response = self.webapp_request(clear_state=True, v=self.v, h=[['h1', 51]], k=[['h1', 0]], d=60, p=11, b=4, s=1, m='1')  # m, p, b and s for getting rid of other features requests
        for i in range(0, 4):
            response = self.webapp_request(h=[['h1', 50]])
        self.assertEqual(response.state['delay'], 120)

        self.webapp_request(path='/admin', command="set", brick='localhost', key='delay', value=30)
        response = self.webapp_request(h=[['h1', 50]])
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 30)
        self.assertIn('sleep_increase_wait', response.state)
        self.assertEqual(response.state['sleep_increase_wait'], 3)


@parameterized_class(getVersionParameter(['sleep', 'latch'], ['temp', 'humid', 'signal']))
class TestFeatureSleepWithLatch(BaseCherryPyTestCase):
    def test_static_delay_after_requests_done(self):
        response = self.webapp_request(clear_state=True, v=self.v, y=['i'], d=60, b=4, s=1)  # b and s for getting rid of other features requests
        self.assertIn('r', response.json)
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 10)

        response = self.webapp_request(x=2, m='1')  # m for getting rid of other features requests
        self.assertNotIn('r', response.json)
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 900)

        for i in range(0, 5):  # should keep at 900 ...
            with self.subTest(i=i):
                response = self.webapp_request()
                self.assertEqual(response.state['delay'], 900)

        response = self.webapp_request(y=['i'])  # ... except there is an request ...
        self.assertIn('r', response.json)
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 10)
        response = self.webapp_request(m='1')  # get rid of sketchMD5 request

        for i in range(5, 9):  # ... back to 900
            with self.subTest(i=i):
                response = self.webapp_request()
                self.assertEqual(response.state['delay'], 900)

    def test_short_delay_after_triggerstate_receivement(self):
        response = self.webapp_request(clear_state=True, v=self.v, l=[0, 1], d=60, b=4, s=1, m='1')  # m, b and s for getting rid of other features requests
        self.assertNotIn('r', response.json)
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 900)

        for i in range(0, 5):  # should keep at 900 ...
            with self.subTest(i=i):
                response = self.webapp_request(l=[0, 1])
                self.assertEqual(response.state['delay'], 900)

        response = self.webapp_request(l=[2, 1])  # ... except there is an triggerstate ...
        self.assertNotIn('r', response.json)
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 20)

        for i in range(5, 9):  # ... back to 900
            with self.subTest(i=i):
                response = self.webapp_request(l=[1, 0])
                self.assertEqual(response.state['delay'], 900)

    def test_admin_override_delay(self):
        response = self.webapp_request(clear_state=True, v=self.v, y=['i'], d=60, b=4, s=1)  # b and s for getting rid of other features requests
        self.assertIn('r', response.json)
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 10)

        response = self.webapp_request(x=2, m='1')  # m for getting rid of other features requests
        self.assertNotIn('r', response.json)
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 900)

        self.webapp_request(path='/admin', command="set", brick='localhost', key='delay', value=30)
        response = self.webapp_request()
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 30)
        self.assertIn('sleep_increase_wait', response.state)
        self.assertEqual(response.state['sleep_increase_wait'], 3)


@parameterized_class(getVersionParameter(['sleep', 'signal'], ['temp', 'humid']))
class TestFeatureSleepWithSignal(BaseCherryPyTestCase):
    def test_signal_state_dependend_delays(self):
        response = self.webapp_request(clear_state=True, v=self.v, d=60, s=2, b=4, m='1')  # m and b for getting rid of other requests
        self.assertNotIn('r', response.json)
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 120)  # by default all signals are set to 0

        self.webapp_request(path='/admin', command="set", signal='localhost_0', key='signal', value=1)
        response = self.webapp_request()
        self.assertNotIn('r', response.json)
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 60)  # now there is one 1 state

        response = self.webapp_request()
        self.assertNotIn('r', response.json)
        self.assertEqual(response.state['delay'], 60)  # nothing changed

        self.webapp_request(path='/admin', command="set", signal='localhost_0', key='signal', value=0)
        response = self.webapp_request()
        self.assertNotIn('r', response.json)
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 120)  # everything back to 0

        response = self.webapp_request()
        self.assertNotIn('r', response.json)
        self.assertEqual(response.state['delay'], 120)  # nothing changed again

    def test_admin_override_delay(self):
        response = self.webapp_request(clear_state=True, v=self.v, y=['i'], d=60, s=2, b=4)  # b for getting rid of other requests
        self.assertIn('r', response.json)
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 10)

        response = self.webapp_request(x=2, m='1')  # m for getting rid of other requests
        self.assertNotIn('r', response.json)
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 120)

        self.webapp_request(path='/admin', command="set", brick='localhost', key='delay', value=30)
        response = self.webapp_request()
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 30)
        self.assertIn('sleep_increase_wait', response.state)
        self.assertEqual(response.state['sleep_increase_wait'], 3)
