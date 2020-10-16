from ._wrapper import *
from freezegun import freeze_time
from datetime import datetime, timedelta


class TestCronInterface(BaseCherryPyTestCase):
    def test_offline_brick(self):
        rolling_time = datetime.now() - timedelta(hours=2)
        with freeze_time(rolling_time):
            response = self.webapp_request(clear_state=True, v='1.0', f=[])
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
