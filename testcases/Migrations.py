from ._wrapper import *
from helpers.current_version import current_brickserver_version
from helpers.migrations import exec_migrate
from connector.mongodb import mongoDB, util_get, util_save, brick_get, brick_save, temp_sensor_get, temp_sensor_save, latch_get, latch_save


# building a brick to be migrated
migrate_test_brick = {
    '_id': 'migrate_test',
    'features': ['sleep', 'bat'],
    'version': {'all': 1, 'os': 1, 'sleep': 1, 'bat': 1},
    'sleep_delay': 120
}


class TestMigrations(BaseCherryPyTestCase):
    def test_fresh_installation_detected(self):
        response = self.webapp_request(clear_state=True)
        self.assertEqual(exec_migrate(current_brickserver_version, True), 'fresh_installation')

    def test_from_v000_to_v060(self):
        response = self.webapp_request(clear_state=True)
        last_migration = util_get('last_migration')
        last_migration['version'] = '0.0.0'
        util_save(last_migration)

        brick_save(migrate_test_brick)
        temp_sensor_save({'_id': 's1'})
        latch_save({'_id': 'migrate_test_0'})
        # create some dummy objects, that create collections to be tested
        mongoDB().events.replace_one({'_id': 'e1'}, {'_id': 'e1'}, True)
        mongoDB().event_data.replace_one({'_id': 'ed1'}, {'_id': 'ed1'}, True)
        exec_migrate('0.6.0', True)

        self.assertEqual(util_get('last_migration')['version'], '0.6.0')

        # check if brick has been migrated
        brick = brick_get('migrate_test')
        temp_sensor = temp_sensor_get('s1')
        latch = latch_get('migrate_test', 0)
        #  from 010 stuff
        self.assertIn('features', brick)
        self.assertNotIn('version', brick)
        self.assertIn('all', list(brick['features'].keys()))
        #  from 030 stuff
        self.assertIsNone(brick['bat_init_ts'])
        self.assertIsNone(brick['bat_init_voltage'])
        self.assertIsNone(brick['bat_runtime_prediction'])
        #  from 042 stuff
        self.assertIn('disables', temp_sensor)
        self.assertIn('disables', latch)
        #  from 050 stuff
        self.assertIn('events', brick)
        self.assertIn('ip', brick)
        self.assertIn('bat_solar_charging', brick)
        self.assertIn('init_ts', brick)
        self.assertIn('events', mongoDB().list_collection_names())
        self.assertIn('event_data', mongoDB().list_collection_names())

    def test_from_v000_to_current(self):
        response = self.webapp_request(clear_state=True)
        last_migration = util_get('last_migration')
        last_migration['version'] = '0.0.0'
        util_save(last_migration)

        brick_save(migrate_test_brick)
        # create some dummy objects, that create collections to be tested
        mongoDB().events.replace_one({'_id': 'e1'}, {'_id': 'e1'}, True)
        mongoDB().event_data.replace_one({'_id': 'ed1'}, {'_id': 'ed1'}, True)
        exec_migrate(current_brickserver_version, True)

        self.assertEqual(util_get('last_migration')['version'], current_brickserver_version)

        # check if brick has been migrated
        brick = brick_get('migrate_test')
        #  < 060 stuff is not relevant, as this is covered on a different test
        #  from 061 stuff
        self.assertNotIn('events', mongoDB().list_collection_names())
        self.assertNotIn('event_data', mongoDB().list_collection_names())
        self.assertIn('delay', brick)
        self.assertNotIn('sleep_delay', brick)
        self.assertEqual(brick['delay'], 120)
