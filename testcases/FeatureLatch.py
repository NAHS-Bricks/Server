from ._wrapper import *


@parameterized_class(getVersionParameter('latch'))
class TestFeatureLatch(BaseCherryPyTestCase):
    def test_latch_states_are_stored(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        self.assertIn('latch_count', response.state)
        self.assertEqual(response.state['latch_count'], 0)

        response = self.webapp_request(l=[0])
        self.assertEqual(response.state['latch_count'], 1)
        self.assertIn('localhost_0', response.latches)
        self.assertEqual(response.latches['localhost_0']['last_state'], 0)

        response = self.webapp_request(l=[1, 0])
        self.assertEqual(response.state['latch_count'], 2)
        self.assertIn('localhost_0', response.latches)
        self.assertIn('localhost_1', response.latches)
        self.assertEqual(response.latches['localhost_0']['last_state'], 1)
        self.assertEqual(response.latches['localhost_0']['prev_state'], 0)
        self.assertEqual(response.latches['localhost_1']['last_state'], 0)

        response = self.webapp_request(l=[2, 3])
        self.assertEqual(response.state['latch_count'], 2)
        self.assertEqual(response.latches['localhost_0']['last_state'], 2)
        self.assertEqual(response.latches['localhost_0']['prev_state'], 1)
        self.assertEqual(response.latches['localhost_1']['last_state'], 3)
        self.assertEqual(response.latches['localhost_1']['prev_state'], 0)

        response = self.webapp_request(l=[0, 1, 2, 3, 4, 5, 0, 1, 2])
        self.assertEqual(response.state['latch_count'], 9)  # there shouldn't be a limitation on how many latches are possible by BrickServer
        self.assertIn('localhost_0', response.latches)
        self.assertIn('localhost_1', response.latches)
        self.assertIn('localhost_2', response.latches)
        self.assertIn('localhost_3', response.latches)
        self.assertIn('localhost_4', response.latches)
        self.assertIn('localhost_5', response.latches)
        self.assertIn('localhost_6', response.latches)
        self.assertIn('localhost_7', response.latches)
        self.assertIn('localhost_8', response.latches)

    def test_trigger_are_added_and_transmitted(self):
        response = self.webapp_request(clear_state=True, v=self.v, l=[0, 0])
        self.assertNotIn('t', response.json)

        self.webapp_request(path='/admin', command='set', latch='localhost_0', key='add_trigger', value=0)
        response = self.webapp_request()
        self.assertIn('t', response.json)
        self.assertEqual(response.json['t'], [[0], []])

        self.webapp_request(path='/admin', command='set', latch='localhost_1', key='add_trigger', value=0)
        self.webapp_request(path='/admin', command='set', latch='localhost_1', key='add_trigger', value=1)
        response = self.webapp_request()
        self.assertIn('t', response.json)
        self.assertEqual(response.json['t'], [[0], [0, 1]])

        self.webapp_request(path='/admin', command='set', latch='localhost_0', key='add_trigger', value=3)
        self.webapp_request(path='/admin', command='set', latch='localhost_0', key='add_trigger', value=2)
        response = self.webapp_request()
        self.assertIn('t', response.json)
        self.assertEqual(response.json['t'], [[0, 2, 3], [0, 1]])  # triggers should be sorted

        self.webapp_request(path='/admin', command='set', latch='localhost_0', key='add_trigger', value=3)
        response = self.webapp_request()
        self.assertIn('t', response.json)
        self.assertEqual(response.json['t'], [[0, 2, 3], [0, 1]])  # adding a trigger twice should not change anything

        response = self.webapp_request()
        self.assertNotIn('t', response.json)  # triggers should not be retransmitted, just once after a change

        response = self.webapp_request(y=['i'])
        self.assertIn('t', response.json)
        self.assertEqual(response.json['t'], [[0, 2, 3], [0, 1]])  # but transmitt them after an init

    def test_trigger_are_removed_and_transmitted(self):
        response = self.webapp_request(clear_state=True, v=self.v, l=[0, 0])
        self.assertNotIn('t', response.json)

        self.webapp_request(path='/admin', command='set', latch='localhost_0', key='add_trigger', value=0)
        self.webapp_request(path='/admin', command='set', latch='localhost_0', key='add_trigger', value=1)
        self.webapp_request(path='/admin', command='set', latch='localhost_1', key='add_trigger', value=0)
        self.webapp_request(path='/admin', command='set', latch='localhost_1', key='add_trigger', value=1)
        response = self.webapp_request()
        self.assertIn('t', response.json)
        self.assertEqual(response.json['t'], [[0, 1], [0, 1]])

        self.webapp_request(path='/admin', command='set', latch='localhost_0', key='del_trigger', value=0)
        response = self.webapp_request()
        self.assertIn('t', response.json)
        self.assertEqual(response.json['t'], [[1], [0, 1]])

        self.webapp_request(path='/admin', command='set', latch='localhost_0', key='del_trigger', value=1)
        self.webapp_request(path='/admin', command='set', latch='localhost_1', key='del_trigger', value=1)
        response = self.webapp_request()
        self.assertIn('t', response.json)
        self.assertEqual(response.json['t'], [[], [0]])

        response = self.webapp_request()
        self.assertNotIn('t', response.json)  # triggers should not be retransmitted, just once after a change

        response = self.webapp_request(y=['i'])
        self.assertIn('t', response.json)
        self.assertEqual(response.json['t'], [[], [0]])  # but transmitt them after an init

    def test_add_trigger_valid_values(self):
        response = self.webapp_request(clear_state=True, v=self.v, l=[0])
        response = self.webapp_request(path='/admin', command='set', latch='localhost_0', key='add_trigger', value=-1)
        self.assertEqual(response.json['s'], 7)
        response = self.webapp_request(path='/admin', command='set', latch='localhost_0', key='add_trigger', value=0)
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', latch='localhost_0', key='add_trigger', value=1)
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', latch='localhost_0', key='add_trigger', value=2)
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', latch='localhost_0', key='add_trigger', value=3)
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', latch='localhost_0', key='add_trigger', value=4)
        self.assertEqual(response.json['s'], 7)

    def test_del_trigger_valid_values(self):
        response = self.webapp_request(clear_state=True, v=self.v, l=[0])
        response = self.webapp_request(path='/admin', command='set', latch='localhost_0', key='del_trigger', value=-1)
        self.assertEqual(response.json['s'], 7)
        response = self.webapp_request(path='/admin', command='set', latch='localhost_0', key='del_trigger', value=0)
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', latch='localhost_0', key='del_trigger', value=1)
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', latch='localhost_0', key='del_trigger', value=2)
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', latch='localhost_0', key='del_trigger', value=3)
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', latch='localhost_0', key='del_trigger', value=4)
        self.assertEqual(response.json['s'], 7)

    def test_latch_desc_is_stored(self):
        response = self.webapp_request(clear_state=True, v=self.v, l=[0, 0])
        self.assertIsNone(response.latches['localhost_0']['desc'])
        self.assertIsNone(response.latches['localhost_1']['desc'])

        response = self.webapp_request(path='/admin', command='set', latch='localhost_0', key='desc', value='latch1')
        self.assertEqual(response.json['s'], 0)
        self.assertEqual(response.latches['localhost_0']['desc'], 'latch1')
        self.assertIsNone(response.latches['localhost_1']['desc'])

        response = self.webapp_request(path='/admin', command='set', latch='localhost_1', key='desc', value='latch2')
        self.assertEqual(response.json['s'], 0)
        self.assertEqual(response.latches['localhost_0']['desc'], 'latch1')
        self.assertEqual(response.latches['localhost_1']['desc'], 'latch2')

        response = self.webapp_request(path='/admin', command='set', latch='localhost_0', key='desc', value='latchX')
        self.assertEqual(response.json['s'], 0)
        self.assertEqual(response.latches['localhost_0']['desc'], 'latchX')
        self.assertEqual(response.latches['localhost_1']['desc'], 'latch2')

    def test_valid_state_desc_states(self):
        response = self.webapp_request(clear_state=True, v=self.v, l=[0])
        response = self.webapp_request(path="/admin", command='set', latch='localhost_0', key='state_desc', state=-1, value='not used')
        self.assertEqual(response.json['s'], 7)
        response = self.webapp_request(path="/admin", command='set', latch='localhost_0', key='state_desc', state=0, value='not used')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path="/admin", command='set', latch='localhost_0', key='state_desc', state=1, value='not used')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path="/admin", command='set', latch='localhost_0', key='state_desc', state=2, value='not used')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path="/admin", command='set', latch='localhost_0', key='state_desc', state=3, value='not used')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path="/admin", command='set', latch='localhost_0', key='state_desc', state=4, value='not used')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path="/admin", command='set', latch='localhost_0', key='state_desc', state=5, value='not used')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path="/admin", command='set', latch='localhost_0', key='state_desc', state=6, value='not used')
        self.assertEqual(response.json['s'], 7)

    def test_state_desc_is_stored(self):
        response = self.webapp_request(clear_state=True, v=self.v, l=[0, 0])
        response = self.webapp_request(path="/admin", command='set', latch='localhost_0', key='state_desc', state=0, value='state1')
        self.assertEqual(response.latches['localhost_0']['states_desc'][0], 'state1')
        self.assertEqual(response.latches['localhost_1']['states_desc'][0], 'low')
        response = self.webapp_request(path="/admin", command='set', latch='localhost_0', key='state_desc', state=1, value='state2')
        self.assertEqual(response.latches['localhost_0']['states_desc'][1], 'state2')
        self.assertEqual(response.latches['localhost_1']['states_desc'][1], 'high')
        response = self.webapp_request(path="/admin", command='set', latch='localhost_0', key='state_desc', state=2, value='state3')
        self.assertEqual(response.latches['localhost_0']['states_desc'][2], 'state3')
        self.assertEqual(response.latches['localhost_1']['states_desc'][2], 'falling-edge')
        response = self.webapp_request(path="/admin", command='set', latch='localhost_0', key='state_desc', state=3, value='state4')
        self.assertEqual(response.latches['localhost_0']['states_desc'][3], 'state4')
        self.assertEqual(response.latches['localhost_1']['states_desc'][3], 'rising-edge')
        response = self.webapp_request(path="/admin", command='set', latch='localhost_0', key='state_desc', state=4, value='state5')
        self.assertEqual(response.latches['localhost_0']['states_desc'][4], 'state5')
        self.assertEqual(response.latches['localhost_1']['states_desc'][4], 'rising-bump')
        response = self.webapp_request(path="/admin", command='set', latch='localhost_0', key='state_desc', state=5, value='state6')
        self.assertEqual(response.latches['localhost_0']['states_desc'][5], 'state6')
        self.assertEqual(response.latches['localhost_1']['states_desc'][5], 'falling-bump')
        # check again that no other state have been affected
        self.assertEqual(response.latches['localhost_0']['states_desc'][0], 'state1')
        self.assertEqual(response.latches['localhost_0']['states_desc'][1], 'state2')
        self.assertEqual(response.latches['localhost_0']['states_desc'][2], 'state3')
        self.assertEqual(response.latches['localhost_0']['states_desc'][3], 'state4')
        self.assertEqual(response.latches['localhost_0']['states_desc'][4], 'state5')
        self.assertEqual(response.latches['localhost_1']['states_desc'][0], 'low')
        self.assertEqual(response.latches['localhost_1']['states_desc'][1], 'high')
        self.assertEqual(response.latches['localhost_1']['states_desc'][2], 'falling-edge')
        self.assertEqual(response.latches['localhost_1']['states_desc'][3], 'rising-edge')
        self.assertEqual(response.latches['localhost_1']['states_desc'][4], 'rising-bump')

    def test_get_latch(self):  # via AdminInterface
        response = self.webapp_request(clear_state=True, v=self.v, l=[0, 1])

        response = self.webapp_request(path='/admin', command='get_latch', latch='localhost_0')
        self.assertIn('latch', response.json)
        self.assertIn('_id', response.json['latch'])
        self.assertEqual(response.json['latch']['_id'], 'localhost_0')
        self.assertIn('last_state', response.json['latch'])
        self.assertEqual(response.json['latch']['last_state'], 0)

        response = self.webapp_request(path='/admin', command='get_latch', latch='localhost_1')
        self.assertIn('latch', response.json)
        self.assertIn('_id', response.json['latch'])
        self.assertEqual(response.json['latch']['_id'], 'localhost_1')
        self.assertIn('last_state', response.json['latch'])
        self.assertEqual(response.json['latch']['last_state'], 1)

    def test_delete_brick_with_latches(self):
        response = self.webapp_request(clear_state=True, v=self.v, l=[1, 2])
        self.assertNotEqual(response.state, {})
        self.assertIn('localhost_0', response.latches)
        self.assertIn('localhost_1', response.latches)
        response = self.webapp_request(path="/admin", command='delete_brick', brick='localhost')
        self.assertIn('deleted', response.json)
        self.assertEqual(response.json['deleted']['brick'], 'localhost')
        self.assertIn('localhost_0', response.json['deleted']['latches'])
        self.assertIn('localhost_1', response.json['deleted']['latches'])
        self.assertEqual(response.state, {})
        self.assertEqual(response.latches, {})

    def test_valid_values_for_disables(self):
        response = self.webapp_request(clear_state=True, v=self.v, l=[1, 2])
        # add disable
        response = self.webapp_request(path='/admin', command='set', latch='localhost_1', key='add_disable', value='ui')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', latch='localhost_1', key='add_disable', value='metric')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', latch='localhost_1', key='add_disable', value='invalid')
        self.assertEqual(response.json['s'], 7)
        # del disable
        response = self.webapp_request(path='/admin', command='set', latch='localhost_1', key='del_disable', value='ui')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', latch='localhost_1', key='del_disable', value='metric')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', latch='localhost_1', key='del_disable', value='invalid')
        self.assertEqual(response.json['s'], 7)

    def test_disables_are_stored(self):
        response = self.webapp_request(clear_state=True, v=self.v, l=[1, 2])
        self.assertEqual(len(response.latches['localhost_1']['disables']), 0)
        response = self.webapp_request(path='/admin', command='set', latch='localhost_1', key='add_disable', value='ui')
        self.assertEqual(len(response.latches['localhost_1']['disables']), 1)
        self.assertIn('ui', response.latches['localhost_1']['disables'])
        response = self.webapp_request(path='/admin', command='set', latch='localhost_1', key='add_disable', value='ui')  # no change allready in list
        self.assertEqual(len(response.latches['localhost_1']['disables']), 1)
        self.assertIn('ui', response.latches['localhost_1']['disables'])
        response = self.webapp_request(path='/admin', command='set', latch='localhost_1', key='add_disable', value='metric')
        self.assertEqual(len(response.latches['localhost_1']['disables']), 2)
        self.assertIn('ui', response.latches['localhost_1']['disables'])
        self.assertIn('metric', response.latches['localhost_1']['disables'])
        response = self.webapp_request(path='/admin', command='set', latch='localhost_1', key='del_disable', value='ui')
        self.assertEqual(len(response.latches['localhost_1']['disables']), 1)
        self.assertIn('metric', response.latches['localhost_1']['disables'])
        response = self.webapp_request(path='/admin', command='set', latch='localhost_1', key='del_disable', value='ui')  # no change allready removed
        self.assertEqual(len(response.latches['localhost_1']['disables']), 1)
        self.assertIn('metric', response.latches['localhost_1']['disables'])
        response = self.webapp_request(path='/admin', command='set', latch='localhost_1', key='del_disable', value='metric')
        self.assertEqual(len(response.latches['localhost_1']['disables']), 0)
