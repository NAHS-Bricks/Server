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
