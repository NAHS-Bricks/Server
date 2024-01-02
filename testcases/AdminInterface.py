from ._wrapper import *
from connector.mongodb import fwmetadata_save
from connector.s3 import firmware_exists

admininterface_versions = [['os', 1.0], ['all', 1.0]]


class TestAdminInterface(BaseCherryPyTestCase):
    def test_invalid_command(self):
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

    def test_invalid_signal(self):
        response = self.webapp_request(clear_state=True, v=admininterface_versions)
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path="/admin", command="set", signal="unknown_0", key='somekey', value='somevalue')
        self.assertEqual(response.json['s'], 20)

    def test_invalid_fanctl(self):
        response = self.webapp_request(clear_state=True, v=admininterface_versions)
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path="/admin", command="set", fanctl="unknown_0", key='somekey', value='somevalue')
        self.assertEqual(response.json['s'], 40)

    def test_invalid_heater(self):
        response = self.webapp_request(clear_state=True, v=admininterface_versions)
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path="/admin", command="set", heater="unknown", key='somekey', value='somevalue')
        self.assertEqual(response.json['s'], 44)

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
        response = self.webapp_request(path="/admin", command='get_heater')  # heater is missing in data
        self.assertEqual(response.json['s'], 42)
        response = self.webapp_request(path="/admin", command='get_fanctl')  # fanctl is missing in data
        self.assertEqual(response.json['s'], 41)
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
        response = self.webapp_request(ignore_brick_id=True, path="/admin", command='set', key='heater', value=0)  # heater is missing in data
        self.assertEqual(response.json['s'], 42)
        response = self.webapp_request(ignore_brick_id=True, path='/admin', command='set', key='bat_solar_charging', value=True)  # brick is missing in data
        self.assertEqual(response.json['s'], 11)
        response = self.webapp_request(ignore_brick_id=True, path='/admin', command='set', key='sleep_disabled', value=True)  # brick is missing in data
        self.assertEqual(response.json['s'], 11)
        response = self.webapp_request(ignore_brick_id=True, path='/admin', command='set', key='bat_adc5V', value=800)  # brick is missing in data
        self.assertEqual(response.json['s'], 11)
        response = self.webapp_request(ignore_brick_id=True, path='/admin', command='set', key='otaupdate', value='requested')  # brick is missing in data
        self.assertEqual(response.json['s'], 11)
        response = self.webapp_request(ignore_brick_id=True, path='/admin', command='set', key='fanctl_mode', value=0)  # fanctl is missing in data
        self.assertEqual(response.json['s'], 41)
        response = self.webapp_request(ignore_brick_id=True, path='/admin', command='set', key='fanctl_duty', value=50)  # fanctl is missing in data
        self.assertEqual(response.json['s'], 41)
        response = self.webapp_request(ignore_brick_id=True, path='/admin', command='set', key='fanctl_state', value=0)  # fanctl is missing in data
        self.assertEqual(response.json['s'], 41)

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

    def test_set_heater_without_feature_heat(self):
        response = self.webapp_request(clear_state=True, v=admininterface_versions + [['heat', 1]])  # indirectly create heater object, to be able to find it by adminInterface later on
        response = self.webapp_request(v=admininterface_versions)  # now remove the feature from brick
        self.assertNotIn('heat', response.state['features'])
        self.assertIn('localhost', response.heaters)
        response = self.webapp_request(path="/admin", command='set', heater='localhost', key='heater', value=0)
        self.assertEqual(response.json['s'], 43)

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
        self.assertEqual(len(response.json['features']), 7)
        self.assertIn('temp', response.json['features'])
        self.assertIn('humid', response.json['features'])
        self.assertIn('bat', response.json['features'])
        self.assertIn('sleep', response.json['features'])
        self.assertIn('latch', response.json['features'])
        self.assertIn('signal', response.json['features'])
        self.assertIn('heat', response.json['features'])

    def test_getting_fwmetadata(self):
        response = self.webapp_request(clear_state=True)
        fwmetadata_save({'brick_type': 1, 'version': '202112301800', 'sketchMD5': '1234', 'content': {'fw': 1}})
        fwmetadata_save({'brick_type': 1, 'version': '202112301900', 'sketchMD5': '5678', 'content': {'fw': 2}})
        fwmetadata_save({'brick_type': 2, 'version': '202112302000', 'sketchMD5': '1234', 'content': {'fw': 3}})

        response = self.webapp_request(path="/admin", command='get_firmwares')
        self.assertEqual(len(response.json['firmwares']), 3)
        response = self.webapp_request(path="/admin", command='get_firmwares', brick_type=1)
        self.assertEqual(len(response.json['firmwares']), 2)
        response = self.webapp_request(path="/admin", command='get_firmwares', brick_type=2)
        self.assertEqual(len(response.json['firmwares']), 1)
        response = self.webapp_request(path="/admin", command='get_firmwares', brick_type=3)
        self.assertEqual(len(response.json['firmwares']), 0)

        response = self.webapp_request(path="/admin", command='get_firmware')  # missing specifiers
        self.assertEqual(response.json['s'], 37)
        response = self.webapp_request(path="/admin", command='get_firmware', brick_type=1)  # missing specifiers
        self.assertEqual(response.json['s'], 37)

        response = self.webapp_request(path="/admin", command='get_firmware', version='202112301800')  # missing specifiers
        self.assertEqual(response.json['s'], 37)
        response = self.webapp_request(path="/admin", command='get_firmware', version='202112301800', brick_type=1)
        self.assertEqual(response.json['s'], 0)
        self.assertEqual(response.json['firmware']['content']['fw'], 1)
        response = self.webapp_request(path="/admin", command='get_firmware', version='202112301800', brick_type=2)
        self.assertEqual(response.json['s'], 0)
        self.assertIsNone(response.json['firmware'])

        response = self.webapp_request(path="/admin", command='get_firmware', sketchmd5='1234')  # missing specifiers
        self.assertEqual(response.json['s'], 37)
        response = self.webapp_request(path="/admin", command='get_firmware', sketchmd5='1234', brick_type=1)
        self.assertEqual(response.json['s'], 0)
        self.assertEqual(response.json['firmware']['content']['fw'], 1)
        response = self.webapp_request(path="/admin", command='get_firmware', sketchmd5='1234', brick_type=2)
        self.assertEqual(response.json['s'], 0)
        self.assertEqual(response.json['firmware']['content']['fw'], 3)
        response = self.webapp_request(path="/admin", command='get_firmware', sketchmd5='5678', brick_type=2)
        self.assertEqual(response.json['s'], 0)
        self.assertIsNone(response.json['firmware'])

        response = self.webapp_request(path="/admin", command='get_firmware', latest=1)
        self.assertEqual(response.json['s'], 0)
        self.assertEqual(response.json['firmware']['content']['fw'], 2)
        response = self.webapp_request(path="/admin", command='get_firmware', latest=2)
        self.assertEqual(response.json['s'], 0)
        self.assertEqual(response.json['firmware']['content']['fw'], 3)
        response = self.webapp_request(path="/admin", command='get_firmware', latest=3)
        self.assertEqual(response.json['s'], 0)
        self.assertIsNone(response.json['firmware'])

    def test_fetching_firmware(self):
        test_versions = [['os', 2], ['all', 1]]
        test_bricktype = 1
        test_sketchMD5 = '1234'
        test_version = ''
        response = self.webapp_request(clear_state=True, v=test_versions, x=test_bricktype, m=test_sketchMD5)
        response = self.webapp_request(path="/admin", command='fetch_firmware')  # invalid value for what
        self.assertEqual(response.json['s'], 7)
        response = self.webapp_request(path="/admin", command='fetch_firmware', what='invalid')  # invalid value for what
        self.assertEqual(response.json['s'], 7)
        response = self.webapp_request(path="/admin", command='get_count', item='firmwares')
        self.assertEqual(response.json['count'], 0)

        # latest
        response = self.webapp_request(path="/admin", command='fetch_firmware', what='latest')  # no brick_type (so for all used brick_types)
        response = self.webapp_request(path="/admin", command='get_count', item='firmwares')
        self.assertEqual(response.json['count'], 1)
        response = self.webapp_request(path="/admin", command='get_firmware', latest=test_bricktype)
        self.assertNotEqual(response.json['firmware']['sketchMD5'], test_sketchMD5)
        test_sketchMD5 = response.json['firmware']['sketchMD5']  # saving for later use
        test_version = response.json['firmware']['version']  # saving for later use

        response = self.webapp_request(clear_state=True, v=test_versions, x=test_bricktype, m=test_sketchMD5)
        response = self.webapp_request(path="/admin", command='get_count', item='firmwares')
        self.assertEqual(response.json['count'], 0)
        response = self.webapp_request(path="/admin", command='fetch_firmware', what='latest', brick_type=test_bricktype)  # now just for this brick_type
        response = self.webapp_request(path="/admin", command='get_count', item='firmwares')
        self.assertEqual(response.json['count'], 1)
        response = self.webapp_request(path="/admin", command='get_firmware', latest=test_bricktype)
        self.assertEqual(response.json['firmware']['sketchMD5'], test_sketchMD5)

        self.assertNotEqual(test_bricktype, 2)
        response = self.webapp_request(path="/admin", command='fetch_firmware', what='latest', brick_type=2)  # now for a brick_type that is not used, but firmware should be pulled
        response = self.webapp_request(path="/admin", command='get_count', item='firmwares')
        self.assertEqual(response.json['count'], 2)
        response = self.webapp_request(path="/admin", command='get_firmware', latest=2)
        self.assertNotEqual(response.json['firmware']['sketchMD5'], test_sketchMD5)

        # used
        response = self.webapp_request(clear_state=True, v=test_versions, x=test_bricktype, m=test_sketchMD5)
        response = self.webapp_request(path="/admin", command='get_count', item='firmwares')
        self.assertEqual(response.json['count'], 0)
        response = self.webapp_request(path="/admin", command='fetch_firmware', what='used')  # for all available bricks (in use)
        response = self.webapp_request(path="/admin", command='get_count', item='firmwares')
        self.assertEqual(response.json['count'], 1)
        response = self.webapp_request(path="/admin", command='get_firmware', latest=test_bricktype)
        self.assertEqual(response.json['firmware']['sketchMD5'], test_sketchMD5)

        response = self.webapp_request(clear_state=True, v=test_versions, x=test_bricktype, m=test_sketchMD5)
        response = self.webapp_request(path="/admin", command='get_count', item='firmwares')
        self.assertEqual(response.json['count'], 0)
        response = self.webapp_request(path="/admin", command='fetch_firmware', what='used', brick='localhost')  # for a specific brick
        response = self.webapp_request(path="/admin", command='get_count', item='firmwares')
        self.assertEqual(response.json['count'], 1)
        response = self.webapp_request(path="/admin", command='get_firmware', latest=test_bricktype)
        self.assertEqual(response.json['firmware']['sketchMD5'], test_sketchMD5)

        # specific
        response = self.webapp_request(path="/admin", command='fetch_firmware', what='specific', version=test_version)  # brick_type is missing
        self.assertEqual(response.json['s'], 38)
        response = self.webapp_request(path="/admin", command='fetch_firmware', what='specific', brick_type=test_bricktype)  # verison is missing
        self.assertEqual(response.json['s'], 39)

        response = self.webapp_request(clear_state=True, v=test_versions, x=test_bricktype, m=test_sketchMD5)
        response = self.webapp_request(path="/admin", command='get_count', item='firmwares')
        self.assertEqual(response.json['count'], 0)
        response = self.webapp_request(path="/admin", command='fetch_firmware', what='specific', brick_type=test_bricktype, version=test_version)  # not yet fetched
        self.assertEqual(len(response.json['fetched']['metadata']), 1)
        response = self.webapp_request(path="/admin", command='get_count', item='firmwares')
        self.assertEqual(response.json['count'], 1)
        response = self.webapp_request(path="/admin", command='get_firmware', latest=test_bricktype)
        self.assertEqual(response.json['firmware']['sketchMD5'], test_sketchMD5)

        response = self.webapp_request(path="/admin", command='fetch_firmware', what='specific', brick_type=test_bricktype, version=test_version)  # allready fetched
        self.assertEqual(len(response.json['fetched']['metadata']), 0)
        response = self.webapp_request(path="/admin", command='get_count', item='firmwares')
        self.assertEqual(response.json['count'], 1)

        # bin
        response = self.webapp_request(path="/admin", command='fetch_firmware', what='bin', version=test_version)  # brick_type is missing
        self.assertEqual(response.json['s'], 38)

        response = self.webapp_request(clear_state=True, v=test_versions, x=test_bricktype, m=test_sketchMD5)
        response = self.webapp_request(path="/admin", command='fetch_firmware', what='specific', brick_type=test_bricktype, version=test_version)  # pre fetching metadata
        response = self.webapp_request(path="/admin", command='get_count', item='firmwares')
        self.assertEqual(response.json['count'], 1)
        response = self.webapp_request(path="/admin", command='get_firmware', latest=test_bricktype)
        self.assertFalse(response.json['firmware']['bin'])  # bin not yet fetched
        response = self.webapp_request(path="/admin", command='fetch_firmware', what='bin', brick_type=test_bricktype, version=test_version)  # fetching bin with metadata present
        response = self.webapp_request(path="/admin", command='get_count', item='firmwares')
        self.assertEqual(response.json['count'], 1)
        response = self.webapp_request(path="/admin", command='get_firmware', latest=test_bricktype)
        self.assertTrue(response.json['firmware']['bin'])  # bin now fetched

        response = self.webapp_request(clear_state=True, v=test_versions, x=test_bricktype, m=test_sketchMD5)
        response = self.webapp_request(path="/admin", command='get_count', item='firmwares')
        self.assertEqual(response.json['count'], 0)
        response = self.webapp_request(path="/admin", command='fetch_firmware', what='bin', brick_type=test_bricktype)  # fetching bin with metadata not present (should fetch both)
        self.assertEqual(len(response.json['fetched']['firmware']), 1)  # reports bin fethed
        response = self.webapp_request(path="/admin", command='get_count', item='firmwares')
        self.assertEqual(response.json['count'], 1)  # metadata fetched
        response = self.webapp_request(path="/admin", command='get_firmware', latest=test_bricktype)
        self.assertTrue(response.json['firmware']['bin'])  # bin also fetched

        response = self.webapp_request(path="/admin", command='fetch_firmware', what='bin', brick_type=test_bricktype, version=test_version)  # bin and metadata allready presend should fetch nothing
        self.assertEqual(len(response.json['fetched']['firmware']), 0)  # nothing fetched report

    def test_deleteing_firmware(self):
        test_versions = [['os', 2], ['all', 1]]
        response = self.webapp_request(clear_state=True, v=test_versions, x=1, m='5678')

        # prepare data to be deleted
        response = self.webapp_request(path="/admin", command='fetch_firmware', what='bin', brick_type=1)
        response = self.webapp_request(path="/admin", command='fetch_firmware', what='bin', brick_type=2)
        response = self.webapp_request(path="/admin", command='get_count', item='firmwares')
        self.assertEqual(response.json['count'], 2)
        response = self.webapp_request(path="/admin", command='get_firmware', latest=1)
        self.assertTrue(response.json['firmware']['bin'])
        test_1_version = response.json['firmware']['version']   # saving for later use
        response = self.webapp_request(path="/admin", command='get_firmware', latest=2)
        self.assertTrue(response.json['firmware']['bin'])
        test_2_version = response.json['firmware']['version']  # saving for later use
        fwmetadata_save({'brick_type': 1, 'version': '202112301800', 'sketchMD5': '1234', 'content': {'fw': 1}})
        fwmetadata_save({'brick_type': 1, 'version': '202112301900', 'sketchMD5': '5678', 'content': {'fw': 2}})
        fwmetadata_save({'brick_type': 2, 'version': '202112302000', 'sketchMD5': '1234', 'content': {'fw': 3}})
        response = self.webapp_request(path="/admin", command='get_count', item='firmwares')
        self.assertEqual(response.json['count'], 5)

        # specifiers missing
        response = self.webapp_request(path="/admin", command='delete_firmware')
        self.assertEqual(response.json['s'], 37)

        # only_bin
        response = self.webapp_request(path="/admin", command='get_firmware', brick_type=1, version=test_1_version)
        self.assertTrue(response.json['firmware']['bin'])
        response = self.webapp_request(path="/admin", command='delete_firmware', brick_type=1, version=test_1_version, bin_only=True)
        response = self.webapp_request(path="/admin", command='get_count', item='firmwares')
        self.assertEqual(response.json['count'], 5)
        response = self.webapp_request(path="/admin", command='get_firmware', brick_type=1, version=test_1_version)
        self.assertFalse(response.json['firmware']['bin'])
        response = self.webapp_request(path="/admin", command='delete_firmware', brick_type=1, version=test_1_version)  # cleaning out remaining metadata
        response = self.webapp_request(path="/admin", command='get_count', item='firmwares')
        self.assertEqual(response.json['count'], 4)

        # bin and metadata in one go
        self.assertTrue(firmware_exists(brick_type=2, version=test_2_version))
        response = self.webapp_request(path="/admin", command='delete_firmware', brick_type=2, version=test_2_version)
        response = self.webapp_request(path="/admin", command='get_count', item='firmwares')
        self.assertEqual(response.json['count'], 3)
        self.assertFalse(firmware_exists(brick_type=2, version=test_2_version))

        # with brick_type and version specified
        response = self.webapp_request(path="/admin", command='delete_firmware', brick_type=1, version='202112301800')
        response = self.webapp_request(path="/admin", command='get_count', item='firmwares')
        self.assertEqual(response.json['count'], 2)

        # with brick_type and sketchMD5 specified
        response = self.webapp_request(path="/admin", command='delete_firmware', brick_type=2, sketchmd5='1234')
        response = self.webapp_request(path="/admin", command='get_count', item='firmwares')
        self.assertEqual(response.json['count'], 1)

        # with latest specified
        response = self.webapp_request(path="/admin", command='delete_firmware', latest=1)
        response = self.webapp_request(path="/admin", command='get_count', item='firmwares')
        self.assertEqual(response.json['count'], 0)
