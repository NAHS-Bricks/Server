from ._wrapper import *
from connector.mongodb import fanctl_exists, fanctl_count, fanctl_get, brick_exists
from connector.influxdb import influxDB
from libfaketime import fake_time
from datetime import datetime, timedelta


@parameterized_class(getVersionParameter('fanctl'))
class TestFeatureFanctl(BaseCherryPyTestCase):
    def test_fanctl_are_created(self):
        # if a state is delivered for a fanctl that does not exist it should be created
        response = self.webapp_request(clear_state=True, y=['i'], v=self.v)
        self.assertEqual(fanctl_count(), 0)
        response = self.webapp_request(fs=[[64, 1, 20], [65, 0, 0]])
        self.assertEqual(fanctl_count(), 2)
        self.assertTrue(fanctl_exists('localhost', '0x40'))
        self.assertTrue(fanctl_exists('localhost', 65))
        response = self.webapp_request(fs=[[64, 1, 20], [65, 0, 0], [67, 0, 0]])
        self.assertEqual(fanctl_count(), 3)
        self.assertTrue(fanctl_exists('localhost', '0x43'))
        # even this should create one
        response = self.webapp_request(fs=[[68, 0, 0]])
        self.assertEqual(fanctl_count(), 4)
        self.assertTrue(fanctl_exists('localhost', '0x44'))

    def test_fanctl_are_not_deleted(self):
        # if a fanctl is not delivered while the init-Flag is True the corresponding fanclt should NOT be deleted
        with fake_time(datetime.now() - timedelta(seconds=10)):
            response = self.webapp_request(clear_state=True, v=self.v, fs=[[64, 1, 20], [65, 0, 0], [66, 0, 0]])
            self.assertEqual(fanctl_count(), 3)
            self.assertTrue(fanctl_exists('localhost', '0x40'))
            self.assertTrue(fanctl_exists('localhost', '0x41'))
            self.assertTrue(fanctl_exists('localhost', '0x42'))
        # due to the init just one fanctl should be left
        response = self.webapp_request(y=['i'], fs=[[65, 0, 0]])
        self.assertEqual(fanctl_count(), 3)
        self.assertTrue(fanctl_exists('localhost', '0x40'))
        self.assertTrue(fanctl_exists('localhost', '0x41'))
        self.assertTrue(fanctl_exists('localhost', '0x42'))
        # also no deletion without init-Flag
        response = self.webapp_request(fs=[[65, 0, 0]])
        self.assertEqual(fanctl_count(), 3)
        self.assertTrue(fanctl_exists('localhost', '0x40'))
        self.assertTrue(fanctl_exists('localhost', '0x41'))
        self.assertTrue(fanctl_exists('localhost', '0x42'))

    def test_state_and_rps_is_stored(self):
        response = self.webapp_request(clear_state=True, y=['i'], v=self.v)
        self.assertEqual(fanctl_count(), 0)

        response = self.webapp_request(fs=[[64, 1, 20], [65, 0, 0]])
        self.assertEqual(fanctl_count(), 2)
        self.assertTrue(fanctl_exists('localhost', '0x40'))
        self.assertTrue(fanctl_exists('localhost', '0x41'))
        f1 = fanctl_get('localhost', '0x40')
        self.assertEqual(f1['state'], 1)
        self.assertEqual(f1['last_rps'], 20)
        self.assertIsNotNone(f1['last_ts'])
        f2 = fanctl_get('localhost', '0x41')
        self.assertEqual(f2['state'], 0)
        self.assertEqual(f2['last_rps'], 0)
        self.assertIsNotNone(f2['last_ts'])

        response = self.webapp_request(fs=[[64, 0, 0], [65, 1, 15]])
        f1 = fanctl_get('localhost', '0x40')
        self.assertEqual(f1['state'], 0)
        self.assertEqual(f1['last_rps'], 0)
        f2 = fanctl_get('localhost', '0x41')
        self.assertEqual(f2['state'], 1)
        self.assertEqual(f2['last_rps'], 15)

    def test_mode_is_requested_and_stored(self):
        response = self.webapp_request(clear_state=True, y=['i'], v=self.v)
        if 'r' in response.json:
            self.assertNotIn(13, response.json['r'])

        response = self.webapp_request(fs=[[64, 1, 20], [65, 0, 0]])
        self.assertIn('r', response.json)
        self.assertIn(13, response.json['r'])

        response = self.webapp_request(fs=[[64, 1, 20], [65, 0, 0]], fm=[[64, -1], [65, 0]])
        if 'r' in response.json:
            self.assertNotIn(13, response.json['r'])
        self.assertTrue(fanctl_exists('localhost', '0x40'))
        self.assertTrue(fanctl_exists('localhost', '0x41'))
        f1 = fanctl_get('localhost', '0x40')
        self.assertEqual(f1['mode'], -1)
        self.assertIsNotNone(f1['mode_transmitted_ts'])
        f2 = fanctl_get('localhost', '0x41')
        self.assertEqual(f2['mode'], 0)
        self.assertIsNotNone(f2['mode_transmitted_ts'])

        response = self.webapp_request(fs=[[64, 1, 20], [65, 0, 0], [66, 1, 10]])
        self.assertIn('r', response.json)
        self.assertIn(13, response.json['r'])

        response = self.webapp_request(fs=[[64, 1, 20], [65, 0, 0], [66, 1, 10]], fm=[[64, 1], [65, 1], [66, 2]])
        if 'r' in response.json:
            self.assertNotIn(13, response.json['r'])
        self.assertTrue(fanctl_exists('localhost', '0x42'))
        f1 = fanctl_get('localhost', '0x40')
        self.assertEqual(f1['mode'], 1)
        self.assertIsNotNone(f1['mode_transmitted_ts'])
        f2 = fanctl_get('localhost', '0x41')
        self.assertEqual(f2['mode'], 1)
        self.assertIsNotNone(f2['mode_transmitted_ts'])
        f3 = fanctl_get('localhost', '0x42')
        self.assertEqual(f3['mode'], 2)
        self.assertIsNotNone(f3['mode_transmitted_ts'])

        response = self.webapp_request(y=['i'], fs=[[64, 1, 20], [65, 0, 0], [66, 1, 10]])
        self.assertIn('r', response.json)
        self.assertIn(13, response.json['r'])

        response = self.webapp_request(fs=[[64, 1, 20], [65, 0, 0], [66, 1, 10]])
        if 'r' in response.json:
            self.assertNotIn(13, response.json['r'])

    def test_get_fanctl(self):  # via AdminInterface
        response = self.webapp_request(clear_state=True, v=self.v, fs=[[64, 1, 20], [65, 0, 0]])

        response = self.webapp_request(path='/admin', command='get_fanctl', fanctl='localhost_64')
        self.assertIn('fanctl', response.json)
        self.assertIn('_id', response.json['fanctl'])
        self.assertEqual(response.json['fanctl']['_id'], 'localhost_0x40')
        self.assertIn('state', response.json['fanctl'])
        self.assertEqual(response.json['fanctl']['state'], 1)
        self.assertIn('last_rps', response.json['fanctl'])
        self.assertEqual(response.json['fanctl']['last_rps'], 20)

        response = self.webapp_request(path='/admin', command='get_fanctl', fanctl='localhost_65')
        self.assertIn('fanctl', response.json)
        self.assertIn('_id', response.json['fanctl'])
        self.assertEqual(response.json['fanctl']['_id'], 'localhost_0x41')
        self.assertIn('state', response.json['fanctl'])
        self.assertEqual(response.json['fanctl']['state'], 0)
        self.assertIn('last_rps', response.json['fanctl'])
        self.assertEqual(response.json['fanctl']['last_rps'], 0)

        # should again return the first one, now addressed in HEX notation
        response = self.webapp_request(path='/admin', command='get_fanctl', fanctl='localhost_0x40')
        self.assertIn('fanctl', response.json)
        self.assertIn('_id', response.json['fanctl'])
        self.assertEqual(response.json['fanctl']['_id'], 'localhost_0x40')
        self.assertIn('state', response.json['fanctl'])
        self.assertEqual(response.json['fanctl']['state'], 1)
        self.assertIn('last_rps', response.json['fanctl'])
        self.assertEqual(response.json['fanctl']['last_rps'], 20)

    def test_set_mode(self):  # via AdminInterface
        response = self.webapp_request(clear_state=True, y=['i'], v=self.v, fs=[[64, 1, 20], [65, 0, 0], [66, 1, 10]], fm=[[64, 1], [65, 1], [66, 2]])
        f1 = fanctl_get('localhost', '0x40')
        self.assertEqual(f1['mode'], 1)
        self.assertIsNotNone(f1['mode_transmitted_ts'])

        # invalid value should not change anything
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='fanctl_mode', value=3)
        self.assertEqual(response.json['s'], 7)
        f1 = fanctl_get('localhost', '0x40')
        self.assertEqual(f1['mode'], 1)
        self.assertIsNotNone(f1['mode_transmitted_ts'])

        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='fanctl_mode', value=0)
        self.assertEqual(response.json['s'], 0)
        f1 = fanctl_get('localhost', '0x40')
        self.assertEqual(f1['mode'], 0)
        self.assertIsNone(f1['mode_transmitted_ts'])

        response = self.webapp_request(fs=[[64, 1, 20], [65, 0, 0], [66, 1, 10]])
        self.assertIn('fm', response.json)
        self.assertEqual(len(response.json['fm']), 1)
        f1 = fanctl_get('localhost', '0x40')
        self.assertEqual(f1['mode'], 0)
        self.assertIsNotNone(f1['mode_transmitted_ts'])

        # don't send modes again
        response = self.webapp_request(fs=[[64, 1, 20], [65, 0, 0], [66, 1, 10]])
        self.assertNotIn('fm', response.json)

        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='fanctl_mode', value=1)
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x41', key='fanctl_mode', value=0)
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(fs=[[64, 1, 20], [65, 0, 0], [66, 1, 10]])
        self.assertIn('fm', response.json)
        self.assertEqual(len(response.json['fm']), 2)

    def test_set_dutyCycle(self):  # via AdminInterface
        response = self.webapp_request(clear_state=True, y=['i'], v=self.v, fs=[[64, 1, 20]], fm=[[64, -1]])
        f1 = fanctl_get('localhost', '0x40')
        self.assertIsNone(f1['dutyCycle'])
        self.assertIsNone(f1['dutyCycle_transmitted_ts'])

        # invalid value should not change anything
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='fanctl_duty', value=101)
        self.assertEqual(response.json['s'], 7)
        f1 = fanctl_get('localhost', '0x40')
        self.assertIsNone(f1['dutyCycle'])
        self.assertIsNone(f1['dutyCycle_transmitted_ts'])

        # dutyCycle can't be transmitted as long as mode is NOT_SET (-1)
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='fanctl_duty', value=50)
        response = self.webapp_request(fs=[[64, 1, 20]])
        self.assertNotIn('fd', response.json)
        f1 = fanctl_get('localhost', '0x40')
        self.assertEqual(f1['dutyCycle'], 50)
        self.assertIsNone(f1['dutyCycle_transmitted_ts'])

        # now with setting mode, dutyCycle is also transmitted
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='fanctl_mode', value=1)
        response = self.webapp_request(fs=[[64, 1, 20]])
        self.assertIn('fd', response.json)
        self.assertEqual(len(response.json['fd']), 1)
        f1 = fanctl_get('localhost', '0x40')
        self.assertEqual(f1['dutyCycle'], 50)
        self.assertIsNotNone(f1['dutyCycle_transmitted_ts'])

        # but not transmitted again
        response = self.webapp_request(fs=[[64, 1, 20]])
        self.assertNotIn('fd', response.json)

        # and now comes an update
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='fanctl_duty', value=60)
        response = self.webapp_request(fs=[[64, 1, 20]])
        self.assertIn('fd', response.json)

    def test_set_dutyCycle_that_is_not_applied(self):
        # it was encountered, that sometimes the fanctl fails in applying the dutyCycle in this case it should be send again
        response = self.webapp_request(clear_state=True, y=['i'], v=self.v, fs=[[64, 0, 0]], fm=[[64, 0]])
        f1 = fanctl_get('localhost', '0x40')
        self.assertIsNone(f1['dutyCycle'])
        self.assertIsNone(f1['dutyCycle_transmitted_ts'])
        self.assertIsNone(f1['state_should'])

        # setting dutyCycle issues transmission
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='fanctl_duty', value=50)
        response = self.webapp_request(fs=[[64, 0, 0]])
        self.assertIn('fd', response.json)
        self.assertEqual(len(response.json['fd']), 1)
        f1 = fanctl_get('localhost', '0x40')
        self.assertEqual(f1['dutyCycle'], 50)
        self.assertIsNotNone(f1['dutyCycle_transmitted_ts'])
        self.assertEqual(f1['state_should'], 1)  # state_should is set to 1 as a consequence of setting dutyCycle

        # if applying dutyCycle failed it is send again
        response = self.webapp_request(fs=[[64, 0, 0]])
        self.assertIn('fd', response.json)
        self.assertEqual(len(response.json['fd']), 1)

        # now it was applyed and dutyCycle is not send again
        response = self.webapp_request(fs=[[64, 1, 20]])
        self.assertNotIn('fd', response.json)

        # fanctl lost it's state, dutyCycle is send again
        response = self.webapp_request(fs=[[64, 0, 0]])
        self.assertIn('fd', response.json)
        self.assertEqual(len(response.json['fd']), 1)

    def test_set_state(self):  # via AdminInterface
        response = self.webapp_request(clear_state=True, y=['i'], v=self.v, fs=[[64, 0, 0]], fm=[[64, -1]])
        f1 = fanctl_get('localhost', '0x40')
        self.assertEqual(f1['state'], 0)
        self.assertIsNone(f1['state_should'])

        # invalid value should not change anything
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='fanctl_state', value=2)
        self.assertEqual(response.json['s'], 7)
        f1 = fanctl_get('localhost', '0x40')
        self.assertEqual(f1['state'], 0)
        self.assertIsNone(f1['state_should'])

        # state can't be transmitted as long as mode is NOT_SET (-1)
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='fanctl_state', value=1)
        response = self.webapp_request(fs=[[64, 0, 0]])
        self.assertNotIn('fs', response.json)
        f1 = fanctl_get('localhost', '0x40')
        self.assertEqual(f1['state'], 0)
        self.assertEqual(f1['state_should'], 1)

        # now with setting mode, state is also transmitted
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='fanctl_mode', value=1)
        response = self.webapp_request(fs=[[64, 0, 0]])
        self.assertIn('fs', response.json)
        self.assertEqual(len(response.json['fs']), 1)
        self.assertEqual(response.json['fs'][0][1], 1)
        f1 = fanctl_get('localhost', '0x40')
        self.assertEqual(f1['state'], 0)
        self.assertEqual(f1['state_should'], 1)  # stays here as long as fanctl's state didn't changed to should

        # if the state doesn't change the state is transmitted again
        response = self.webapp_request(fs=[[64, 0, 0]])  # usually this one would now be state 1 but in this test it is still 0
        self.assertIn('fs', response.json)
        self.assertEqual(len(response.json['fs']), 1)
        self.assertEqual(response.json['fs'][0][1], 1)

        # now the fanctl deliveres the desired 1, so the state is not send again
        response = self.webapp_request(fs=[[64, 1, 10]])
        self.assertNotIn('fs', response.json)
        f1 = fanctl_get('localhost', '0x40')
        self.assertEqual(f1['state'], 1)
        self.assertEqual(f1['state_should'], 1)  # but the should value stays, just in case

        # now trying to set fanctl off
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='fanctl_state', value=0)
        response = self.webapp_request(fs=[[64, 1, 10]])
        self.assertIn('fs', response.json)
        self.assertEqual(len(response.json['fs']), 1)
        self.assertEqual(response.json['fs'][0][1], 0)
        f1 = fanctl_get('localhost', '0x40')
        self.assertEqual(f1['state'], 1)
        self.assertEqual(f1['state_should'], 0)

        # which fails, so retransmission of state
        response = self.webapp_request(fs=[[64, 1, 10]])
        self.assertIn('fs', response.json)
        self.assertEqual(len(response.json['fs']), 1)
        self.assertEqual(response.json['fs'][0][1], 0)
        f1 = fanctl_get('localhost', '0x40')
        self.assertEqual(f1['state'], 1)
        self.assertEqual(f1['state_should'], 0)

        # and finally it works
        response = self.webapp_request(fs=[[64, 0, 0]])
        self.assertNotIn('fs', response.json)
        f1 = fanctl_get('localhost', '0x40')
        self.assertEqual(f1['state'], 0)
        self.assertEqual(f1['state_should'], 0)

        # but is flaky, so retransmit state again
        response = self.webapp_request(fs=[[64, 1, 10]])
        self.assertIn('fs', response.json)
        self.assertEqual(len(response.json['fs']), 1)
        self.assertEqual(response.json['fs'][0][1], 0)
        f1 = fanctl_get('localhost', '0x40')
        self.assertEqual(f1['state'], 1)
        self.assertEqual(f1['state_should'], 0)

    def test_set_desc(self):  # via AdminInterface
        response = self.webapp_request(clear_state=True, v=self.v, fs=[[64, 1, 20], [65, 0, 0]])
        f1 = fanctl_get('localhost', '0x40')
        self.assertIsNone(f1['desc'])
        f2 = fanctl_get('localhost', '0x41')
        self.assertIsNone(f2['desc'])

        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='desc', value='fan1')
        self.assertEqual(response.json['s'], 0)
        f1 = fanctl_get('localhost', '0x40')
        self.assertEqual(f1['desc'], 'fan1')

        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_65', key='desc', value='fan2')
        self.assertEqual(response.json['s'], 0)
        f2 = fanctl_get('localhost', '0x41')
        self.assertEqual(f2['desc'], 'fan2')

    def test_delete_brick_with_fanctl(self):  # via AdminInterface
        response = self.webapp_request(clear_state=True, v=self.v, fs=[[64, 1, 20], [65, 0, 0]])
        self.assertTrue(brick_exists('localhost'))
        self.assertTrue(fanctl_exists('localhost', '0x40'))
        self.assertTrue(fanctl_exists('localhost', '0x41'))
        response = self.webapp_request(path="/admin", command='delete_brick', brick='localhost')
        self.assertIn('deleted', response.json)
        self.assertEqual(response.json['deleted']['brick'], 'localhost')
        self.assertIn('localhost_0x40', response.json['deleted']['fanctl'])
        self.assertIn('localhost_0x41', response.json['deleted']['fanctl'])
        self.assertFalse(brick_exists('localhost'))
        self.assertFalse(fanctl_exists('localhost', '0x40'))
        self.assertFalse(fanctl_exists('localhost', '0x41'))

    def test_fanctl_count_is_returned(self):  # via AdminInterface
        response = self.webapp_request(clear_state=True, v=self.v)
        response = self.webapp_request(path='/admin', command='get_count', item='fanctl')
        self.assertIn('count', response.json)
        self.assertEqual(response.json['count'], 0)
        response = self.webapp_request(fs=[[64, 1, 20], [65, 0, 0]])
        response = self.webapp_request(path='/admin', command='get_count', item='fanctl')
        self.assertIn('count', response.json)
        self.assertEqual(response.json['count'], 2)
        response = self.webapp_request(fs=[[64, 1, 20], [65, 0, 0], [66, 0, 0]])
        response = self.webapp_request(path='/admin', command='get_count', item='fanctl')
        self.assertIn('count', response.json)
        self.assertEqual(response.json['count'], 3)
        response = self.webapp_request(path="/admin", command='delete_brick', brick='localhost')
        response = self.webapp_request(path='/admin', command='get_count', item='fanctl')
        self.assertIn('count', response.json)
        self.assertEqual(response.json['count'], 0)

    def test_valid_values_for_disables(self):  # via AdminInterface
        response = self.webapp_request(clear_state=True, v=self.v, fs=[[64, 1, 20]])
        # add disable
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='add_disable', value='ui')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='add_disable', value='metric')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='add_disable', value='mqtt')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='add_disable', value='invalid')
        self.assertEqual(response.json['s'], 7)
        # del disable
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='del_disable', value='ui')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='del_disable', value='metric')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='del_disable', value='mqtt')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='del_disable', value='invalid')
        self.assertEqual(response.json['s'], 7)

    def test_disables_are_stored(self):  # via AdminInterface
        response = self.webapp_request(clear_state=True, v=self.v, fs=[[64, 1, 20]])
        f1 = fanctl_get('localhost', '0x40')
        self.assertEqual(len(f1['disables']), 1)
        self.assertIn('metric', f1['disables'])
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='add_disable', value='metric')  # no change allready in list
        f1 = fanctl_get('localhost', '0x40')
        self.assertEqual(len(f1['disables']), 1)
        self.assertIn('metric', f1['disables'])
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='add_disable', value='ui')
        f1 = fanctl_get('localhost', '0x40')
        self.assertEqual(len(f1['disables']), 2)
        self.assertIn('metric', f1['disables'])
        self.assertIn('ui', f1['disables'])
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='del_disable', value='ui')
        f1 = fanctl_get('localhost', '0x40')
        self.assertEqual(len(f1['disables']), 1)
        self.assertIn('metric', f1['disables'])
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='del_disable', value='ui')  # no change allready removed
        f1 = fanctl_get('localhost', '0x40')
        self.assertEqual(len(f1['disables']), 1)
        self.assertIn('metric', f1['disables'])
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='del_disable', value='metric')
        f1 = fanctl_get('localhost', '0x40')
        self.assertEqual(len(f1['disables']), 0)

    def test_mqtt_messages_are_send(self):
        response = self.webapp_request(clear_state=True, mqtt_test=True, v=self.v, fs=[[64, 1, 20], [65, 0, 0]], fm=[[64, 0], [65, 0]])
        self.assertIn('brick/localhost/fanctl/localhost_0x40/state 1', response.mqtt)
        self.assertIn('brick/localhost/fanctl/localhost_0x40/rps 20', response.mqtt)
        self.assertIn('brick/localhost/fanctl/localhost_0x41/state 0', response.mqtt)
        self.assertIn('brick/localhost/fanctl/localhost_0x41/rps 0', response.mqtt)
        response = self.webapp_request(mqtt_test=True, fs=[[64, 0, 2], [65, 1, 15]])
        self.assertIn('brick/localhost/fanctl/localhost_0x40/state 0', response.mqtt)
        self.assertIn('brick/localhost/fanctl/localhost_0x40/rps 2', response.mqtt)
        self.assertIn('brick/localhost/fanctl/localhost_0x41/state 1', response.mqtt)
        self.assertIn('brick/localhost/fanctl/localhost_0x41/rps 15', response.mqtt)

        # disableing h2 to send mqtt messages
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='add_disable', value='mqtt')
        response = self.webapp_request(mqtt_test=True, fs=[[64, 0, 0], [65, 1, 15]])
        self.assertNotIn('brick/localhost/fanctl/localhost_0x40/state 0', response.mqtt)
        self.assertNotIn('brick/localhost/fanctl/localhost_0x40/rps 0', response.mqtt)
        self.assertIn('brick/localhost/fanctl/localhost_0x41/state 1', response.mqtt)
        self.assertIn('brick/localhost/fanctl/localhost_0x41/rps 15', response.mqtt)

        # enable h2 to send mqtt messages
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='del_disable', value='mqtt')
        response = self.webapp_request(mqtt_test=True, fs=[[64, 0, 0], [65, 1, 15]])
        self.assertIn('brick/localhost/fanctl/localhost_0x40/state 0', response.mqtt)
        self.assertIn('brick/localhost/fanctl/localhost_0x40/rps 0', response.mqtt)
        self.assertIn('brick/localhost/fanctl/localhost_0x41/state 1', response.mqtt)
        self.assertIn('brick/localhost/fanctl/localhost_0x41/rps 15', response.mqtt)

        # test for state transmitted message
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='fanctl_state', value=1)
        response = self.webapp_request(mqtt_test=True, fs=[[64, 0, 0], [65, 1, 15]])
        self.assertIn('brick/localhost/fanctl/localhost_0x40/state 11', response.mqtt)

        # test for duty transmitted message
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='fanctl_duty', value=50)
        response = self.webapp_request(mqtt_test=True, fs=[[64, 1, 0], [65, 1, 15]])
        self.assertIn('brick/localhost/fanctl/localhost_0x40/duty 50', response.mqtt)

    def test_metrics_are_stored(self):
        stmt_state = 'SELECT "state" FROM "brickserver"."8weeks"."fanctl_states" WHERE "brick_id" = \'localhost\' and "fanctl_id" = \'$fid\' ORDER BY time DESC LIMIT 1'
        stmt_state_d = 'SELECT "state" FROM "brickserver"."8weeks"."fanctl_states" WHERE "brick_desc" = \'bl\' and "fanctl_desc" = \'f$fid\' ORDER BY time DESC LIMIT 1'
        stmt_rps = 'SELECT "rps" FROM "brickserver"."8weeks"."fanctl_states" WHERE "brick_id" = \'localhost\' and "fanctl_id" = \'$fid\' ORDER BY time DESC LIMIT 1'
        stmt_duty = 'SELECT "dutyCycle" FROM "brickserver"."8weeks"."fanctl_duty" WHERE "brick_id" = \'localhost\' and "fanctl_id" = \'$fid\' ORDER BY time DESC LIMIT 1'
        stmt_duty_d = 'SELECT "dutyCycle" FROM "brickserver"."8weeks"."fanctl_duty" WHERE "brick_desc" = \'bl\' and "fanctl_desc" = \'f$fid\' ORDER BY time DESC LIMIT 1'
        response = self.webapp_request(clear_state=True, mqtt_test=True, v=self.v, fs=[[64, 1, 20], [65, 0, 0]], fm=[[64, 0], [65, 0]])
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x40', key='del_disable', value='metric')
        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x41', key='del_disable', value='metric')

        response = self.webapp_request(path='/admin', command='set', key='desc', brick='localhost', value='bl')
        response = self.webapp_request(path='/admin', command='set', key='desc', fanctl='localhost_0x40', value='f0x40')
        response = self.webapp_request(path='/admin', command='set', key='desc', fanctl='localhost_0x41', value='f0x41')
        response = self.webapp_request(fs=[[64, 1, 20], [65, 0, 0]])
        time.sleep(0.05)
        self.assertEqual(influxDB.query(stmt_state.replace('$fid', '0x40')).raw['series'][0]['values'][0][1], 1)
        self.assertEqual(influxDB.query(stmt_rps.replace('$fid', '0x40')).raw['series'][0]['values'][0][1], 20)
        self.assertEqual(influxDB.query(stmt_state.replace('$fid', '0x41')).raw['series'][0]['values'][0][1], 0)
        self.assertEqual(influxDB.query(stmt_rps.replace('$fid', '0x41')).raw['series'][0]['values'][0][1], 0)
        # metrics should also be found with their description
        self.assertEqual(influxDB.query(stmt_state_d.replace('$fid', '0x40')).raw['series'][0]['values'][0][1], 1)
        self.assertEqual(influxDB.query(stmt_state_d.replace('$fid', '0x41')).raw['series'][0]['values'][0][1], 0)

        response = self.webapp_request(path='/admin', command='set', fanctl='localhost_0x41', key='fanctl_duty', value=90)
        response = self.webapp_request(fs=[[64, 1, 20], [65, 0, 0]])
        time.sleep(0.05)
        # duty should be logged ...
        self.assertEqual(influxDB.query(stmt_duty.replace('$fid', '0x41')).raw['series'][0]['values'][0][1], 90)
        self.assertEqual(influxDB.query(stmt_duty_d.replace('$fid', '0x41')).raw['series'][0]['values'][0][1], 90)  # also with desc
        # ...  states unchanged
        self.assertEqual(influxDB.query(stmt_state.replace('$fid', '0x40')).raw['series'][0]['values'][0][1], 1)
        self.assertEqual(influxDB.query(stmt_rps.replace('$fid', '0x40')).raw['series'][0]['values'][0][1], 20)
        self.assertEqual(influxDB.query(stmt_state.replace('$fid', '0x41')).raw['series'][0]['values'][0][1], 0)
        self.assertEqual(influxDB.query(stmt_rps.replace('$fid', '0x41')).raw['series'][0]['values'][0][1], 0)

        response = self.webapp_request(fs=[[64, 1, 20], [65, 1, 33]])
        time.sleep(0.05)
        self.assertEqual(influxDB.query(stmt_state.replace('$fid', '0x40')).raw['series'][0]['values'][0][1], 1)
        self.assertEqual(influxDB.query(stmt_rps.replace('$fid', '0x40')).raw['series'][0]['values'][0][1], 20)
        self.assertEqual(influxDB.query(stmt_state.replace('$fid', '0x41')).raw['series'][0]['values'][0][1], 1)
        self.assertEqual(influxDB.query(stmt_rps.replace('$fid', '0x41')).raw['series'][0]['values'][0][1], 33)
