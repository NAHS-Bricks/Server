from ._wrapper import *
from helpers.current_version import current_brickserver_version


class HealthInterface(BaseCherryPyTestCase):

    def test_health_page(self):
        response = self.webapp_request(clear_state=True, method='get')
        self.assertEqual(len(response.json.keys()), 13)
        self.assertEqual(response.json['version'], current_brickserver_version)
        self.assertTrue(response.json['mongodb_connected'])
        self.assertTrue(response.json['influxdb_connected'])
        self.assertTrue(response.json['mqtt_connected'])
        self.assertTrue(response.json['s3_connected'])
        self.assertTrue(response.json['ds_allowed'])
        self.assertTrue(response.json['ds_connected'])
        self.assertEqual(response.json['brick_count'], 0)
        self.assertEqual(response.json['temp_sensor_count'], 0)
        self.assertEqual(response.json['humid_sensor_count'], 0)
        self.assertEqual(response.json['latch_count'], 0)
        self.assertEqual(response.json['signal_count'], 0)
        self.assertEqual(response.json['fwmetadata_count'], 0)
