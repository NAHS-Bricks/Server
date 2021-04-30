from ._wrapper import *
from freezegun import freeze_time
from datetime import datetime, timedelta


class TestCronInterface(BaseCherryPyTestCase):
    def test_offline_brick_without_desc(self):
        rolling_time = datetime.now() - timedelta(hours=2)
        with freeze_time(rolling_time):
            response = self.webapp_request(clear_state=True, v=[['os', 1.0], ['all', 1.0]], f=[])
            response = self.webapp_request(path='/cron')
            self.assertNotIn("Brick localhost didn't send any data within the last hour!", response.telegram)
        rolling_time += timedelta(minutes=1)
        for i in range(0, 29):
            with freeze_time(rolling_time):
                response = self.webapp_request(path='/cron')
                self.assertEqual(response.cron_data['offline_send']['localhost'], False)
                self.assertNotIn("Brick localhost didn't send any data within the last hour!", response.telegram)
            rolling_time += timedelta(minutes=2)
        rolling_time += timedelta(minutes=1)
        with freeze_time(rolling_time):
            response = self.webapp_request(path='/cron')
            self.assertIn("Brick localhost didn't send any data within the last hour!", response.telegram)
            self.assertEqual(response.cron_data['offline_send']['localhost'], True)

        # Test message is not send again
        rolling_time += timedelta(minutes=1)
        with freeze_time(rolling_time):
            response = self.webapp_request(path='/cron')
            self.assertNotIn("Brick localhost didn't send any data within the last hour!", response.telegram)
            self.assertEqual(response.json['s'], 0)

    def test_offline_brick_with_desc(self):
        rolling_time = datetime.now() - timedelta(hours=2)
        with freeze_time(rolling_time):
            response = self.webapp_request(clear_state=True, v=[['os', 1.0], ['all', 1.0]], f=[])
            self.webapp_request(path='/admin', command='set', brick='localhost', key='desc', value='somebrick')
            response = self.webapp_request(path='/cron')
            self.assertNotIn("Brick somebrick didn't send any data within the last hour!", response.telegram)
        rolling_time += timedelta(minutes=1)
        for i in range(0, 29):
            with freeze_time(rolling_time):
                response = self.webapp_request(path='/cron')
                self.assertEqual(response.cron_data['offline_send']['localhost'], False)
                self.assertNotIn("Brick somebrick didn't send any data within the last hour!", response.telegram)
            rolling_time += timedelta(minutes=2)
        rolling_time += timedelta(minutes=1)
        with freeze_time(rolling_time):
            response = self.webapp_request(path='/cron')
            self.assertIn("Brick somebrick didn't send any data within the last hour!", response.telegram)
            self.assertEqual(response.cron_data['offline_send']['localhost'], True)

        # Test message is not send again
        rolling_time += timedelta(minutes=1)
        with freeze_time(rolling_time):
            response = self.webapp_request(path='/cron')
            self.assertNotIn("Brick somebrick didn't send any data within the last hour!", response.telegram)
            self.assertEqual(response.json['s'], 0)

    def test_daily_report(self):
        rolling_time = (datetime.now() - timedelta(days=2)).replace(hour=19, minute=1)
        with freeze_time(rolling_time):
            response = self.webapp_request(clear_state=True, f=['bat'], v=[['os', 1.0], ['all', 1.0], ['bat', 1.0]])
            response = self.webapp_request(b=3.7)
            self.assertEqual(response.state['bat_last_reading'], 3.7)

        # Not 8pm now, so dont send a report
        rolling_time += timedelta(minutes=1)
        with freeze_time(rolling_time):
            response = self.webapp_request(path='/cron')
            self.assertNotIn('Daily-Report', response.telegram)

        # now we are around 8pm, send a message
        rolling_time += timedelta(hours=1)
        with freeze_time(rolling_time):
            response = self.webapp_request(path='/cron')
            self.assertIn('Daily-Report', response.telegram)

        # but don't send it again if allready send
        rolling_time += timedelta(minutes=1)
        with freeze_time(rolling_time):
            response = self.webapp_request(path='/cron')
            self.assertNotIn('Daily-Report', response.telegram)

        # but the day after, it's send again
        rolling_time += timedelta(days=1)
        with freeze_time(rolling_time):
            response = self.webapp_request(path='/cron')
            self.assertIn('Daily-Report', response.telegram)
