from ._wrapper import *
from event.commands import commands as event_command
from connector.mongodb import event_get, event_save, event_data_get, event_data_save


class TestEventCommands(BaseCherryPyTestCase):
    def test_signals_pending(self):
        response = self.webapp_request(clear_state=True, v=[['all', 1], ['os', 1], ['signal', 1]], s=2, y=['i'])
        self.assertIsNotNone(response.signals['localhost_0']['state_transmitted_ts'])
        self.assertIsNotNone(response.signals['localhost_1']['state_transmitted_ts'])

        self.assertFalse(event_command['signals_pending']('notNeeded', None, response.state, None))

        response = self.webapp_request(path='/admin', command='set', signal='localhost_1', key='signal', value=1)  # setting a signal results in a pending
        self.assertTrue(event_command['signals_pending']('notNeeded', None, response.state, None))

        response = self.webapp_request()  # transmitting signals results in not pending
        self.assertFalse(event_command['signals_pending']('notNeeded', None, response.state, None))

    def test_latch_state_match(self):
        response = self.webapp_request(clear_state=True, v=[['all', 1], ['os', 1]])
        ev = event_get()
        ev['brick_id'] = 'localhost'
        ed = event_data_get(ev, 'config')
        self.assertFalse(event_command['latch_state_match'](ev, ed, response.state, None))  # latch not in features

        response = self.webapp_request(v=[['all', 1], ['os', 1], ['latch', 1]], l=[0, 1, 2, 3, 4, 5])
        self.assertFalse(event_command['latch_state_match'](ev, ed, response.state, None))  # expression not in event_data

        ed['expression'] = 1
        event_data_save(ed)
        self.assertFalse(event_command['latch_state_match'](ev, ed, response.state, None))  # expression is not list

        ed['expression'] = [1, 2]
        event_data_save(ed)
        self.assertFalse(event_command['latch_state_match'](ev, ed, response.state, None))  # expression list len is not 3

        ed['expression'] = [1, 'bullshit', 2]
        event_data_save(ed)
        self.assertFalse(event_command['latch_state_match'](ev, ed, response.state, None))  # invalid expression operator

        ed['expression'] = [['0', '==', 0], 'and', ['1', '!=', 0]]
        event_data_save(ed)
        self.assertTrue(event_command['latch_state_match'](ev, ed, response.state, None))

        ed['expression'] = [['0', '>', 0], 'or', ['1', '>', 0]]
        event_data_save(ed)
        self.assertTrue(event_command['latch_state_match'](ev, ed, response.state, None))

        ed['expression'] = [['2', '<=', 1], 'or', ['0', '>=', 1]]
        event_data_save(ed)
        self.assertFalse(event_command['latch_state_match'](ev, ed, response.state, None))

        ed['expression'] = [[['4', '<', 2], 'or', ['3', '<', 2]], 'or', [['2', '<', 2], 'or', ['1', '<', 2]]]
        event_data_save(ed)
        self.assertTrue(event_command['latch_state_match'](ev, ed, response.state, None))
