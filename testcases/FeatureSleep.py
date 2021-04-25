from ._wrapper import *


@parameterized_class(getVersionParameter('sleep', ['temp', 'latch', 'bat']))
class TestFeatureSleep(BaseCherryPyTestCase):
    def test_inactiv_by_its_own(self):
        response = self.webapp_request(clear_state=True, v=self.v)
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


@parameterized_class(getVersionParameter(['sleep', 'bat']))
class TestFeatureSleepWithBat(BaseCherryPyTestCase):
    def test_charging(self):
        response = self.webapp_request(clear_state=True, v=self.v, y=['c'])
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 60)
        self.assertIn('sleep_increase_wait', response.state)
        self.assertEqual(response.state['sleep_increase_wait'], 3)

        for i in range(0, 20):
            with self.subTest(i=i):
                response = self.webapp_request(y=['c'])
                self.assertIn('d', response.json)
                self.assertEqual(response.json['d'], 60)
                self.assertIn('sleep_increase_wait', response.state)
                self.assertEqual(response.state['sleep_increase_wait'], 3)

    def test_charging_standby(self):
        response = self.webapp_request(clear_state=True, v=self.v, y=['s'])
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 60)
        self.assertIn('sleep_increase_wait', response.state)
        self.assertEqual(response.state['sleep_increase_wait'], 3)

        for i in range(0, 20):
            with self.subTest(i=i):
                response = self.webapp_request(y=['s'])
                self.assertIn('d', response.json)
                self.assertEqual(response.json['d'], 60)
                self.assertIn('sleep_increase_wait', response.state)
                self.assertEqual(response.state['sleep_increase_wait'], 3)


@parameterized_class(getVersionParameter(['sleep', 'temp']))
class TestFeatureSleepWithTemp(BaseCherryPyTestCase):
    def test_delay_increase_on_stable_temp(self):
        response = self.webapp_request(clear_state=True, v=self.v, t=[['s1', 25]], c=[['s1', 0]], p=11, b=4)  # b for getting rid of bat_voltage request with feature bat
        self.assertNotIn('d', response.json)
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
        response = self.webapp_request(clear_state=True, v=self.v, t=[['s1', 25]], c=[['s1', 0]], p=11, b=4)  # b for getting rid of bat_voltage request with feature bat
        for i in range(0, 4):
            response = self.webapp_request(t=[['s1', 24]])
        self.assertEqual(response.state['sleep_delay'], 120)
        response = self.webapp_request(t=[['s1', 24.25]])
        self.assertNotIn('d', response.json)
        self.assertEqual(response.state['sleep_delay'], 120)

        response = self.webapp_request(clear_state=True, v=self.v, t=[['s1', 25]], c=[['s1', 0]], p=11, b=4)  # b for getting rid of bat_voltage request with feature bat
        for i in range(0, 7):
            response = self.webapp_request(t=[['s1', 24]])
        self.assertEqual(response.state['sleep_delay'], 180)
        response = self.webapp_request(t=[['s1', 24.25]])
        self.assertNotIn('d', response.json)
        self.assertEqual(response.state['sleep_delay'], 180)

    def test_no_delay_decrease_on_negative_point25_change(self):
        response = self.webapp_request(clear_state=True, v=self.v, t=[['s1', 25]], c=[['s1', 0]], p=11, b=4)  # b for getting rid of bat_voltage request with feature bat
        for i in range(0, 4):
            response = self.webapp_request(t=[['s1', 24]])
        self.assertEqual(response.state['sleep_delay'], 120)
        response = self.webapp_request(t=[['s1', 23.75]])
        self.assertNotIn('d', response.json)
        self.assertEqual(response.state['sleep_delay'], 120)

        response = self.webapp_request(clear_state=True, v=self.v, t=[['s1', 25]], c=[['s1', 0]], p=11, b=4)  # b for getting rid of bat_voltage request with feature bat
        for i in range(0, 7):
            response = self.webapp_request(t=[['s1', 24]])
        self.assertEqual(response.state['sleep_delay'], 180)
        response = self.webapp_request(t=[['s1', 23.75]])
        self.assertNotIn('d', response.json)
        self.assertEqual(response.state['sleep_delay'], 180)

    def test_delay_decrease_on_positive_point26_change(self):
        response = self.webapp_request(clear_state=True, v=self.v, t=[['s1', 25]], c=[['s1', 0]], p=11, b=4)  # b for getting rid of bat_voltage request with feature bat
        for i in range(0, 4):
            response = self.webapp_request(t=[['s1', 24]])
        self.assertEqual(response.state['sleep_delay'], 120)
        response = self.webapp_request(t=[['s1', 24.26]])
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 60)
        self.assertEqual(response.state['sleep_delay'], 60)

        response = self.webapp_request(clear_state=True, v=self.v, t=[['s1', 25]], c=[['s1', 0]], p=11, b=4)  # b for getting rid of bat_voltage request with feature bat
        for i in range(0, 7):
            response = self.webapp_request(t=[['s1', 24]])
        self.assertEqual(response.state['sleep_delay'], 180)
        response = self.webapp_request(t=[['s1', 24.26]])
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 60)
        self.assertEqual(response.state['sleep_delay'], 60)

    def test_delay_decrease_on_negative_point26_change(self):
        response = self.webapp_request(clear_state=True, v=self.v, t=[['s1', 25]], c=[['s1', 0]], p=11, b=4)  # b for getting rid of bat_voltage request with feature bat
        for i in range(0, 4):
            response = self.webapp_request(t=[['s1', 24]])
        self.assertEqual(response.state['sleep_delay'], 120)
        response = self.webapp_request(t=[['s1', 23.74]])
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 60)
        self.assertEqual(response.state['sleep_delay'], 60)

        response = self.webapp_request(clear_state=True, v=self.v, t=[['s1', 25]], c=[['s1', 0]], p=11, b=4)  # b for getting rid of bat_voltage request with feature bat
        for i in range(0, 7):
            response = self.webapp_request(t=[['s1', 24]])
        self.assertEqual(response.state['sleep_delay'], 180)
        response = self.webapp_request(t=[['s1', 23.74]])
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 60)
        self.assertEqual(response.state['sleep_delay'], 60)


@parameterized_class(getVersionParameter(['sleep', 'latch'], ['temp']))
class TestFeatureSleepWithLatch(BaseCherryPyTestCase):
    def test_static_delay_after_requests_done(self):
        response = self.webapp_request(clear_state=True, v=self.v, y=['i'], b=4)  # b for getting rid of bat_voltage request with feature bat
        self.assertIn('r', response.json)
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 60)

        response = self.webapp_request(x=2)
        self.assertNotIn('r', response.json)
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 900)

        for i in range(0, 5):  # should keep at 900 ...
            with self.subTest(i=i):
                response = self.webapp_request()
                self.assertNotIn('r', response.json)
                self.assertIn('d', response.json)
                self.assertEqual(response.json['d'], 900)

        response = self.webapp_request(y=['i'])  # ... except there is an request ...
        self.assertIn('r', response.json)
        self.assertIn('d', response.json)
        self.assertEqual(response.json['d'], 60)

        for i in range(5, 9):  # ... back to 900
            with self.subTest(i=i):
                response = self.webapp_request()
                self.assertNotIn('r', response.json)
                self.assertIn('d', response.json)
                self.assertEqual(response.json['d'], 900)
