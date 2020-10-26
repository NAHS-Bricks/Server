from ._wrapper import *
from freezegun import freeze_time
from datetime import datetime, timedelta


class TestCronInterface(BaseCherryPyTestCase):
    def test_offline_brick(self):
        rolling_time = datetime.now() - timedelta(hours=2)
        with freeze_time(rolling_time):
            response = self.webapp_request(clear_state=True, v=[['os', 1.0], ['all', 1.0]], f=[])
            response = self.webapp_request(path='/cron')
            self.assertNotIn('send any data within the last hour', response.telegram)
        rolling_time += timedelta(minutes=1)
        for i in range(0, 29):
            with freeze_time(rolling_time):
                response = self.webapp_request(path='/cron')
                self.assertEqual(response.cron_data['offline_send']['localhost'], False)
                self.assertNotIn('send any data within the last hour', response.telegram)
            rolling_time += timedelta(minutes=2)
        rolling_time += timedelta(minutes=1)
        with freeze_time(rolling_time):
            response = self.webapp_request(path='/cron')
            self.assertIn('send any data within the last hour', response.telegram)
            self.assertEqual(response.cron_data['offline_send']['localhost'], True)

        # Test message is not send again
        rolling_time += timedelta(minutes=1)
        with freeze_time(rolling_time):
            response = self.webapp_request(path='/cron')
            self.assertNotIn('send any data within the last hour', response.telegram)
            self.assertEqual(response.json['s'], 0)

    def test_dayly_report(self):
        rolling_time = (datetime.now() - timedelta(days=2)).replace(hour=19, minute=1)
        with freeze_time(rolling_time):
            response = self.webapp_request(clear_state=True, f=['bat'], v=[['os', 1.0], ['all', 1.0], ['bat', 1.0]])
            response = self.webapp_request(b=3.7)
            self.assertEqual(response.state['bat_last_reading'], 3.7)

        # Not 8pm now, so dont send a report
        rolling_time += timedelta(minutes=1)
        with freeze_time(rolling_time):
            response = self.webapp_request(path='/cron')
            self.assertNotIn('Dayly-Report', response.telegram)

        # now we are around 8pm, send a message
        rolling_time += timedelta(hours=1)
        with freeze_time(rolling_time):
            response = self.webapp_request(path='/cron')
            self.assertIn('Dayly-Report', response.telegram)

        # but don't send it again if allready send
        rolling_time += timedelta(minutes=1)
        with freeze_time(rolling_time):
            response = self.webapp_request(path='/cron')
            self.assertNotIn('Dayly-Report', response.telegram)

        # but the day after, it's send again
        rolling_time += timedelta(days=1)
        with freeze_time(rolling_time):
            response = self.webapp_request(path='/cron')
            self.assertIn('Dayly-Report', response.telegram)
