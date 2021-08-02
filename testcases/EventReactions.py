from ._wrapper import *
from event.reactions import reactions as event_reaction
from connector.mongodb import event_get, event_save, event_data_get, event_data_save


class TestEventReactions(BaseCherryPyTestCase):
    def test_no_save_methods_used(self):  # reactions are not allowed to use save methods, they have to use the admin interface for saveing operations
        with open('event/reactions.py', 'r') as f:
            for line in f.read().strip().split('\n'):
                if line.strip().startswith('from'):
                    self.assertNotIn('_save', line)

    def test_set_signal_state(self):
        response = self.webapp_request(clear_state=True, v=[['all', 1], ['os', 1], ['signal', 1]], s=2, y=['i'])
        self.assertIsNotNone(response.signals['localhost_0']['state_transmitted_ts'])
        self.assertIsNotNone(response.signals['localhost_1']['state_transmitted_ts'])

        ev = event_get()
        ed = event_data_get(ev, 'config')

        ed = {'_id': ed['_id'], 'signal_id': 'localhost_1'}
        self.assertFalse(event_reaction['set_signal_state'](ev, ed))  # state missing in event_data

        ed = {'_id': ed['_id'], 'state': 1}
        self.assertFalse(event_reaction['set_signal_state'](ev, ed))  # signal_id missing in event_data

        ed = {'_id': ed['_id'], 'signal_id': 'localhost_1', 'state': 1}
        self.assertTrue(event_reaction['set_signal_state'](ev, ed))  # should work, all data present
        response = self.webapp_request(path='/admin', command='get_signal', signal='localhost_1')
        self.assertIsNone(response.json['signal']['state_transmitted_ts'])
        self.assertEqual(response.json['signal']['state'], 1)

        self.assertTrue(event_reaction['set_signal_state'](ev, ed))  # send again to test branch if signal allready in desired state

    def test_trigger_brick(self):
        response = self.webapp_request(clear_state=True, v=[['all', 1], ['os', 1], ['sleep', 1]])
        self.assertEqual(response.state['ip'], '127.0.0.1')

        ev = event_get()
        ed = event_data_get(ev, 'config')

        self.assertFalse(event_reaction['trigger_brick'](ev, ed))  # brick missing in event_data

        ed['brick'] = 'localhost'
        self.assertFalse(event_reaction['trigger_brick'](ev, ed))  # feature sleep present in features (triggering not possible)

        response = self.webapp_request(v=[['all', 1], ['os', 1]])
        self.assertTrue(event_reaction['trigger_brick'](ev, ed))

    def test_math(self):
        self.webapp_request(clear_state=True)
        ev = event_get()
        ev['brick_id'] = 'localhost'
        event_save(ev)
        ed = event_data_get(ev, 'input')

        ed = {'_id': ed['_id'], 'operand': 1, 'event_data_name': 'output', 'event_data_key': 'val'}
        self.assertFalse(event_reaction['math'](ev, ed))  # operator missing in event_data

        ed = {'_id': ed['_id'], 'operator': '+', 'event_data_name': 'output', 'event_data_key': 'val'}
        self.assertFalse(event_reaction['math'](ev, ed))  # operand missing in event_data

        ed = {'_id': ed['_id'], 'operator': '+', 'operand': 1, 'event_data_key': 'val'}
        self.assertFalse(event_reaction['math'](ev, ed))  # event_data_name missing in event_data

        ed = {'_id': ed['_id'], 'operator': '+', 'operand': 1, 'event_data_name': 'output'}
        self.assertFalse(event_reaction['math'](ev, ed))  # event_data_key missing in event_data

        ed = {'_id': ed['_id'], 'operator': '+', 'operand': 1, 'event_data_name': 'output', 'event_data_key': 'val'}
        self.assertTrue(event_reaction['math'](ev, ed))
        self.assertEqual(event_data_get(ev, 'output')['val'], 1)

        ed = {'_id': ed['_id'], 'operator': '-', 'operand': 1, 'event_data_name': 'output', 'event_data_key': 'val'}
        self.assertTrue(event_reaction['math'](ev, ed))
        self.assertEqual(event_data_get(ev, 'output')['val'], 0)

        ed = {'_id': ed['_id'], 'operator': '=', 'operand': 5, 'event_data_name': 'output', 'event_data_key': 'val'}
        self.assertTrue(event_reaction['math'](ev, ed))
        self.assertEqual(event_data_get(ev, 'output')['val'], 5)

        ed = {'_id': ed['_id'], 'operator': '*', 'operand': 3, 'event_data_name': 'output', 'event_data_key': 'val'}
        self.assertTrue(event_reaction['math'](ev, ed))
        self.assertEqual(event_data_get(ev, 'output')['val'], 15)

        ed = {'_id': ed['_id'], 'operator': '/', 'operand': 3, 'event_data_name': 'output', 'event_data_key': 'val'}
        self.assertTrue(event_reaction['math'](ev, ed))
        self.assertEqual(event_data_get(ev, 'output')['val'], 5)

        ed = {'_id': ed['_id'], 'operator': '%', 'operand': 3, 'event_data_name': 'output', 'event_data_key': 'val'}
        self.assertTrue(event_reaction['math'](ev, ed))
        self.assertEqual(event_data_get(ev, 'output')['val'], 2)

        ed = {'_id': ed['_id'], 'operator': 'h', 'operand': 3, 'event_data_name': 'output', 'event_data_key': 'val'}
        self.assertFalse(event_reaction['math'](ev, ed))  # invalid operator

        ed = {'_id': ed['_id'], 'operator': '+', 'operand': 'false', 'event_data_name': 'output', 'event_data_key': 'val'}
        self.assertFalse(event_reaction['math'](ev, ed))  # invalid operand
