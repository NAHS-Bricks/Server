from ._wrapper import *

admininterface_versions = [['os', 1.0], ['all', 1.0]]


class TestAdminInterface(BaseCherryPyTestCase):
    def test_invalid_comand(self):
        response = self.webapp_request(path="/admin", command="bullshit")
        self.assertEqual(response.json['s'], 2)

    def test_invalid_brick(self):
        response = self.webapp_request(clear_state=True, v=admininterface_versions)
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path="/admin", command="get_brick", brick="unknown")
        self.assertEqual(response.json['s'], 3)
        self.assertNotIn('brick', response.json)
        response = self.webapp_request(path="/admin", command="set", brick="unknown", key='somekey', value='somevalue')
        self.assertEqual(response.json['s'], 3)

    def test_invalid_temp_sensor(self):
        response = self.webapp_request(clear_state=True, v=admininterface_versions)
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path="/admin", command="set", temp_sensor="unknown", key='somekey', value='somevalue')
        self.assertEqual(response.json['s'], 8)

    def test_invalid_humid_sensor(self):
        response = self.webapp_request(clear_state=True, v=admininterface_versions)
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path="/admin", command="set", humid_sensor="unknown", key='somekey', value='somevalue')
        self.assertEqual(response.json['s'], 32)

    def test_invalid_latch(self):
        response = self.webapp_request(clear_state=True, v=admininterface_versions)
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path="/admin", command="set", latch="unknown_0", key='somekey', value='somevalue')
        self.assertEqual(response.json['s'], 9)

    def test_forgotten_params(self):
        response = self.webapp_request(clear_state=True, v=admininterface_versions)
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path="/admin")
        self.assertEqual(response.json['s'], 1)
        response = self.webapp_request(ignore_brick_id=True, path="/admin", command='set')
        self.assertEqual(response.json['s'], 4)
        response = self.webapp_request(ignore_brick_id=True, path="/admin", command='set', key='somekey')
        self.assertEqual(response.json['s'], 5)
        response = self.webapp_request(ignore_brick_id=True, path="/admin", command='set', value='somevalue')
        self.assertEqual(response.json['s'], 4)
        response = self.webapp_request(ignore_brick_id=True, path="/admin", command='set', key='temp_precision', value=11)  # brick is missing in data
        self.assertEqual(response.json['s'], 11)
        response = self.webapp_request(ignore_brick_id=True, path="/admin", command='set', key='delay', value=40)  # brick is missing in data
        self.assertEqual(response.json['s'], 11)
        response = self.webapp_request(path="/admin", command='get_brick')  # brick is missing in data
        self.assertEqual(response.json['s'], 11)
        response = self.webapp_request(ignore_brick_id=True, path="/admin", command='delete_brick')  # brick is missing in data
        self.assertEqual(response.json['s'], 11)
        response = self.webapp_request(path="/admin", command='get_temp_sensor')  # temp_sensor is missing in data
        self.assertEqual(response.json['s'], 12)
        response = self.webapp_request(path="/admin", command='get_humid_sensor')  # humid_sensor is missing in data
        self.assertEqual(response.json['s'], 33)
        response = self.webapp_request(path="/admin", command='get_latch')  # latch is missing in data
        self.assertEqual(response.json['s'], 13)
        response = self.webapp_request(path="/admin", command='get_signal')  # signal is missing in data
        self.assertEqual(response.json['s'], 18)
        response = self.webapp_request(ignore_brick_id=True, path="/admin", command='set', key='add_trigger', value=0)  # latch is missing in data
        self.assertEqual(response.json['s'], 13)
        response = self.webapp_request(ignore_brick_id=True, path="/admin", command='set', key='del_trigger', value=0)  # latch is missing in data
        self.assertEqual(response.json['s'], 13)
        response = self.webapp_request(ignore_brick_id=True, path="/admin", command='set', key='desc', value='not used')  # no object given for setting desc
        self.assertEqual(response.json['s'], 14)
        response = self.webapp_request(ignore_brick_id=True, path="/admin", command='set', key='state_desc', value='not used')  # state is missing in data
        self.assertEqual(response.json['s'], 15)
        response = self.webapp_request(ignore_brick_id=True, path="/admin", command='set', key='state_desc', state=0, value='not used')  # no object given for setting state_desc
        self.assertEqual(response.json['s'], 14)
        response = self.webapp_request(ignore_brick_id=True, path="/admin", command='set', key='add_disable', value='ui')  # no object given for adding disable
        self.assertEqual(response.json['s'], 14)
        response = self.webapp_request(ignore_brick_id=True, path="/admin", command='set', key='del_disable', value='ui')  # no object given for deleteing disable
        self.assertEqual(response.json['s'], 14)
        response = self.webapp_request(path="/admin", command='get_count')  # item is missing in data
        self.assertEqual(response.json['s'], 16)
        response = self.webapp_request(path="/admin", command='get_count', item='invalid')  # invalid item given
        self.assertEqual(response.json['s'], 17)
        response = self.webapp_request(ignore_brick_id=True, path="/admin", command='set', key='signal', value=0)  # signal is missing in data
        self.assertEqual(response.json['s'], 18)
        response = self.webapp_request(ignore_brick_id=True, path='/admin', command='set', key='bat_solar_charging', value=True)  # brick is missing in data
        self.assertEqual(response.json['s'], 11)
        response = self.webapp_request(ignore_brick_id=True, path='/admin', command='set', key='sleep_disabled', value=True)  # brick is missing in data
        self.assertEqual(response.json['s'], 11)

    def test_brick_desc(self):
        response = self.webapp_request(clear_state=True, v=admininterface_versions)
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path="/admin", command='set', brick="localhost", key="desc", value='a test host')
        self.assertEqual(response.json['s'], 0)
        self.assertEqual(response.state['desc'], 'a test host')

    def test_get_brick(self):
        response = self.webapp_request(clear_state=True, v=admininterface_versions)
        response = self.webapp_request(path="/admin", command='get_brick', brick='localhost')
        self.assertIn('brick', response.json)
        self.assertEqual(response.json['brick']['_id'], 'localhost')

    def test_get_all_bricks(self):
        response = self.webapp_request(clear_state=True, v=admininterface_versions)
        response = self.webapp_request(path="/admin", command='get_bricks')
        self.assertEqual(response.json['bricks'], ['localhost'])

    def test_delete_brick(self):
        response = self.webapp_request(clear_state=True, v=admininterface_versions)
        self.assertNotEqual(response.state, {})
        response = self.webapp_request(path="/admin", command='delete_brick', brick='localhost')
        self.assertIn('deleted', response.json)
        self.assertEqual(response.json['deleted'], {'brick': 'localhost'})
        self.assertEqual(response.state, {})

    def test_get_version(self):
        response = self.webapp_request(clear_state=True, v=admininterface_versions)
        response = self.webapp_request(path="/admin", command='get_version')
        self.assertIn('version', response.json)
        self.assertGreaterEqual(len(response.json['version'].split('.')), 3)

    def test_get_count_bricks(self):
        response = self.webapp_request(clear_state=True, v=admininterface_versions)
        response = self.webapp_request(path="/admin", command='get_count', item='bricks')
        self.assertIn('count', response.json)
        self.assertEqual(response.json['count'], 1)

    def test_set_temp_precision_without_feature_temp(self):
        response = self.webapp_request(clear_state=True, v=admininterface_versions)
        response = self.webapp_request(path="/admin", command='set', brick='localhost', key='temp_precision', value=11)
        self.assertEqual(response.json['s'], 6)

    def test_set_add_trigger_without_feature_latch(self):
        response = self.webapp_request(clear_state=True, v=admininterface_versions + [['latch', 1.0]], l=[0])  # indirectly create latch object, to be able to find latch object by adminInterface later on
        response = self.webapp_request(v=admininterface_versions)  # now remove the feature from brick
        self.assertNotIn('latch', response.state['features'])
        self.assertIn('localhost_0', response.latches)
        response = self.webapp_request(path="/admin", command='set', latch='localhost_0', key='add_trigger', value=0)
        self.assertEqual(response.json['s'], 10)

    def test_set_del_trigger_without_feature_latch(self):
        response = self.webapp_request(clear_state=True, v=admininterface_versions + [['latch', 1.0]], l=[0])  # indirectly create latch object, to be able to find latch object by adminInterface later on
        response = self.webapp_request(v=admininterface_versions)  # now remove the feature from brick
        self.assertNotIn('latch', response.state['features'])
        self.assertIn('localhost_0', response.latches)
        response = self.webapp_request(path="/admin", command='set', latch='localhost_0', key='del_trigger', value=0)
        self.assertEqual(response.json['s'], 10)

    def test_set_signal_without_feature_signal(self):
        response = self.webapp_request(clear_state=True, v=admininterface_versions + [['signal', 1.0]], s=1)  # indirectly create signal object, to be able to find signal object by adminInterface later on
        response = self.webapp_request(v=admininterface_versions)  # now remove the feature from brick
        self.assertNotIn('signal', response.state['features'])
        self.assertIn('localhost_0', response.signals)
        response = self.webapp_request(path="/admin", command='set', signal='localhost_0', key='signal', value=0)
        self.assertEqual(response.json['s'], 19)

    def test_set_sleep_disabled(self):
        response = self.webapp_request(clear_state=True, v=admininterface_versions)
        response = self.webapp_request(path="/admin", command='set', brick='localhost', key='sleep_disabled', value=0)  # invalid value, needs to be a bool
        self.assertEqual(response.json['s'], 7)
        response = self.webapp_request(path="/admin", command='set', brick='localhost', key='sleep_disabled', value=True)  # sleep not in brick-features
        self.assertEqual(response.json['s'], 34)
        response = self.webapp_request(v=admininterface_versions + [['sleep', 1]])  # add feature sleep, but with wrong version
        response = self.webapp_request(path="/admin", command='set', brick='localhost', key='sleep_disabled', value=True)  # feature version not satisfied (sleep >= 1.01)
        self.assertEqual(response.json['s'], 35)
        response = self.webapp_request(v=admininterface_versions + [['sleep', 1.01]])  # now upgrade feature version to correct one
        response = self.webapp_request(path="/admin", command='set', brick='localhost', key='sleep_disabled', value=True)  # should be fine now
        self.assertEqual(response.json['s'], 0)

    def test_get_features(self):
        response = self.webapp_request(path="/admin", command='get_features')
        self.assertEqual(response.json['s'], 0)
        self.assertEqual(len(response.json['features']), 6)
        self.assertIn('temp', response.json['features'])
        self.assertIn('humid', response.json['features'])
        self.assertIn('bat', response.json['features'])
        self.assertIn('sleep', response.json['features'])
        self.assertIn('latch', response.json['features'])
        self.assertIn('signal', response.json['features'])
