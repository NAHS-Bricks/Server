from ._wrapper import *


@parameterized_class(getVersionParameter('signal'))
class TestFeatureSignal(BaseCherryPyTestCase):
    def test_request_signal_count(self):
        response = self.webapp_request(clear_state=True, v=self.v)  # should request signal_count as it is None
        self.assertIn('r', response.json)
        self.assertIn(7, response.json['r'])
        response = self.webapp_request()  # should re-request signal_count as it is still None
        self.assertIn('r', response.json)
        self.assertIn(7, response.json['r'])
        response = self.webapp_request(s=2)  # should not request signal_count anymore as it's been set
        if 'r' in response.json:
            self.assertNotIn(7, response.json['r'])
        response = self.webapp_request(y=['i'])  # should request signal_count as brick have been initialized
        self.assertIn('r', response.json)
        self.assertIn(7, response.json['r'])
        response = self.webapp_request()  # but no re-request this time
        if 'r' in response.json:
            self.assertNotIn(7, response.json['r'])

    def test_signal_count_is_stored(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        self.assertIsNone(response.state['signal_count'])
        response = self.webapp_request(s=2)
        self.assertEqual(response.state['signal_count'], 2)
        response = self.webapp_request(s=3)
        self.assertEqual(response.state['signal_count'], 3)

    def test_count_of_signals_in_db_is_aligned_to_signal_count(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        self.assertEqual(len(response.signals), 0)
        response = self.webapp_request(s=2)
        self.assertEqual(len(response.signals), 2)
        response = self.webapp_request(s=3)
        self.assertEqual(len(response.signals), 3)
        response = self.webapp_request(s=2)
        self.assertEqual(len(response.signals), 2)

    def test_delete_brick_with_signals(self):
        response = self.webapp_request(clear_state=True, v=self.v, s=2)
        self.assertNotEqual(response.state, {})
        self.assertEqual(len(response.signals), 2)
        self.assertIn('localhost_0', response.signals)
        self.assertIn('localhost_1', response.signals)
        response = self.webapp_request(path="/admin", command='delete_brick', brick='localhost')
        self.assertIn('deleted', response.json)
        self.assertEqual(response.json['deleted']['brick'], 'localhost')
        self.assertIn('localhost_0', response.json['deleted']['signals'])
        self.assertIn('localhost_0', response.json['deleted']['signals'])
        self.assertEqual(response.state, {})
        self.assertEqual(len(response.signals), 0)

    def test_signal_count_is_returned(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        response = self.webapp_request(path='/admin', command='get_count', item='signals')
        self.assertIn('count', response.json)
        self.assertEqual(response.json['count'], 0)
        response = self.webapp_request(s=2)
        response = self.webapp_request(path='/admin', command='get_count', item='signals')
        self.assertIn('count', response.json)
        self.assertEqual(response.json['count'], 2)
        response = self.webapp_request(s=3)
        response = self.webapp_request(path='/admin', command='get_count', item='signals')
        self.assertIn('count', response.json)
        self.assertEqual(response.json['count'], 3)
        response = self.webapp_request(s=2)
        response = self.webapp_request(path='/admin', command='get_count', item='signals')
        self.assertIn('count', response.json)
        self.assertEqual(response.json['count'], 2)

    def test_set_state_api(self):
        response = self.webapp_request(clear_state=True, v=self.v, s=2)
        self.assertEqual(response.signals['localhost_0']['state'], 0)
        self.assertIsNone(response.signals['localhost_0']['state_set_ts'])
        self.assertIsNone(response.signals['localhost_0']['state_transmitted_ts'])
        self.assertEqual(response.signals['localhost_1']['state'], 0)
        self.assertIsNone(response.signals['localhost_1']['state_set_ts'])
        self.assertIsNone(response.signals['localhost_1']['state_transmitted_ts'])

        response = self.webapp_request(path='/admin', command='set', key='signal', signal='localhost_0', value=1)
        self.assertEqual(response.signals['localhost_0']['state'], 1)
        self.assertIsNotNone(response.signals['localhost_0']['state_set_ts'])
        self.assertIsNone(response.signals['localhost_0']['state_transmitted_ts'])
        self.assertEqual(response.signals['localhost_1']['state'], 0)
        self.assertIsNone(response.signals['localhost_1']['state_set_ts'])
        self.assertIsNone(response.signals['localhost_1']['state_transmitted_ts'])

        response = self.webapp_request(path='/admin', command='set', key='signal', signal='localhost_1', value=1)
        self.assertEqual(response.signals['localhost_0']['state'], 1)
        self.assertIsNotNone(response.signals['localhost_0']['state_set_ts'])
        self.assertIsNone(response.signals['localhost_0']['state_transmitted_ts'])
        self.assertEqual(response.signals['localhost_1']['state'], 1)
        self.assertIsNotNone(response.signals['localhost_1']['state_set_ts'])
        self.assertIsNone(response.signals['localhost_1']['state_transmitted_ts'])

        response = self.webapp_request(path='/admin', command='set', key='signal', signal='localhost_0', value=0)
        self.assertEqual(response.signals['localhost_0']['state'], 0)
        self.assertIsNotNone(response.signals['localhost_0']['state_set_ts'])
        self.assertIsNone(response.signals['localhost_0']['state_transmitted_ts'])
        self.assertEqual(response.signals['localhost_1']['state'], 1)
        self.assertIsNotNone(response.signals['localhost_1']['state_set_ts'])
        self.assertIsNone(response.signals['localhost_1']['state_transmitted_ts'])

        # invalid signal
        response = self.webapp_request(path='/admin', command='set', key='signal', signal='localhost_2', value=1)
        self.assertEqual(response.json['s'], 20)

        # invalid values
        response = self.webapp_request(path='/admin', command='set', key='signal', signal='localhost_1', value=-1)
        self.assertEqual(response.json['s'], 7)
        response = self.webapp_request(path='/admin', command='set', key='signal', signal='localhost_1', value=2)
        self.assertEqual(response.json['s'], 7)

    def test_signal_states_are_transmitted(self):
        response = self.webapp_request(clear_state=True, v=self.v, s=2)
        self.assertNotIn('o', response.json)
        self.assertIsNone(response.signals['localhost_0']['state_transmitted_ts'])
        self.assertIsNone(response.signals['localhost_1']['state_transmitted_ts'])

        response = self.webapp_request(y=['i'])
        self.assertIn('o', response.json)
        self.assertEqual(response.json['o'], [0, 0])
        self.assertIsNotNone(response.signals['localhost_0']['state_transmitted_ts'])
        self.assertIsNotNone(response.signals['localhost_1']['state_transmitted_ts'])

        response = self.webapp_request(path='/admin', command='set', key='signal', signal='localhost_0', value=1)
        self.assertIsNone(response.signals['localhost_0']['state_transmitted_ts'])
        self.assertIsNotNone(response.signals['localhost_1']['state_transmitted_ts'])
        response = self.webapp_request()
        self.assertIn('o', response.json)
        self.assertEqual(response.json['o'], [1, 0])
        self.assertIsNotNone(response.signals['localhost_0']['state_transmitted_ts'])
        self.assertIsNotNone(response.signals['localhost_1']['state_transmitted_ts'])

        response = self.webapp_request(path='/admin', command='set', key='signal', signal='localhost_0', value=0)
        response = self.webapp_request(path='/admin', command='set', key='signal', signal='localhost_1', value=1)
        self.assertIsNone(response.signals['localhost_0']['state_transmitted_ts'])
        self.assertIsNone(response.signals['localhost_1']['state_transmitted_ts'])
        response = self.webapp_request()
        self.assertIn('o', response.json)
        self.assertEqual(response.json['o'], [0, 1])
        self.assertIsNotNone(response.signals['localhost_0']['state_transmitted_ts'])
        self.assertIsNotNone(response.signals['localhost_1']['state_transmitted_ts'])

    def test_signal_desc_is_stored(self):
        response = self.webapp_request(clear_state=True, v=self.v, s=2)
        self.assertIsNone(response.signals['localhost_0']['desc'])
        self.assertIsNone(response.signals['localhost_1']['desc'])

        response = self.webapp_request(path='/admin', command='set', signal='localhost_0', key='desc', value='sig1')
        self.assertEqual(response.json['s'], 0)
        self.assertEqual(response.signals['localhost_0']['desc'], 'sig1')
        self.assertIsNone(response.signals['localhost_1']['desc'])

        response = self.webapp_request(path='/admin', command='set', signal='localhost_1', key='desc', value='sig2')
        self.assertEqual(response.json['s'], 0)
        self.assertEqual(response.signals['localhost_0']['desc'], 'sig1')
        self.assertEqual(response.signals['localhost_1']['desc'], 'sig2')

        response = self.webapp_request(path='/admin', command='set', signal='localhost_0', key='desc', value='sigX')
        self.assertEqual(response.json['s'], 0)
        self.assertEqual(response.signals['localhost_0']['desc'], 'sigX')
        self.assertEqual(response.signals['localhost_1']['desc'], 'sig2')

    def test_get_signal(self):  # via AdminInterface
        response = self.webapp_request(clear_state=True, v=self.v, s=2)
        response = self.webapp_request(path='/admin', command='set', key='signal', signal='localhost_0', value=1)
        response = self.webapp_request(path='/admin', command='set', signal='localhost_1', key='desc', value='sig2')

        response = self.webapp_request(path='/admin', command='get_signal', signal='localhost_0')
        self.assertIn('signal', response.json)
        self.assertIn('_id', response.json['signal'])
        self.assertEqual(response.json['signal']['_id'], 'localhost_0')
        self.assertEqual(response.json['signal']['state'], 1)
        self.assertIsNone(response.json['signal']['desc'])

        response = self.webapp_request(path='/admin', command='get_signal', signal='localhost_1')
        self.assertIn('signal', response.json)
        self.assertIn('_id', response.json['signal'])
        self.assertEqual(response.json['signal']['_id'], 'localhost_1')
        self.assertEqual(response.json['signal']['state'], 0)
        self.assertEqual(response.json['signal']['desc'], 'sig2')

    def test_valid_state_desc_states(self):
        response = self.webapp_request(clear_state=True, v=self.v, s=1)
        response = self.webapp_request(path="/admin", command='set', signal='localhost_0', key='state_desc', state=-1, value='not used')
        self.assertEqual(response.json['s'], 7)
        response = self.webapp_request(path="/admin", command='set', signal='localhost_0', key='state_desc', state=0, value='not used')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path="/admin", command='set', signal='localhost_0', key='state_desc', state=1, value='not used')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path="/admin", command='set', signal='localhost_0', key='state_desc', state=2, value='not used')
        self.assertEqual(response.json['s'], 7)

    def test_state_desc_is_stored(self):
        response = self.webapp_request(clear_state=True, v=self.v, s=2)
        response = self.webapp_request(path="/admin", command='set', signal='localhost_0', key='state_desc', state=0, value='state1')
        self.assertEqual(response.signals['localhost_0']['states_desc'][0], 'state1')
        self.assertEqual(response.signals['localhost_1']['states_desc'][0], 'off')
        response = self.webapp_request(path="/admin", command='set', signal='localhost_0', key='state_desc', state=1, value='state2')
        self.assertEqual(response.signals['localhost_0']['states_desc'][1], 'state2')
        self.assertEqual(response.signals['localhost_1']['states_desc'][1], 'on')
        # check again that no other state have been affected
        self.assertEqual(response.signals['localhost_0']['states_desc'][0], 'state1')
        self.assertEqual(response.signals['localhost_0']['states_desc'][1], 'state2')
        self.assertEqual(response.signals['localhost_1']['states_desc'][0], 'off')
        self.assertEqual(response.signals['localhost_1']['states_desc'][1], 'on')

    def test_valid_values_for_disables(self):
        response = self.webapp_request(clear_state=True, v=self.v, s=2)
        # add disable
        response = self.webapp_request(path='/admin', command='set', signal='localhost_1', key='add_disable', value='ui')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', signal='localhost_1', key='add_disable', value='metric')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', signal='localhost_1', key='add_disable', value='invalid')
        self.assertEqual(response.json['s'], 7)
        # del disable
        response = self.webapp_request(path='/admin', command='set', signal='localhost_1', key='del_disable', value='ui')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', signal='localhost_1', key='del_disable', value='metric')
        self.assertEqual(response.json['s'], 0)
        response = self.webapp_request(path='/admin', command='set', signal='localhost_1', key='del_disable', value='invalid')
        self.assertEqual(response.json['s'], 7)

    def test_disables_are_stored(self):
        response = self.webapp_request(clear_state=True, v=self.v, s=2)
        self.assertEqual(len(response.signals['localhost_1']['disables']), 0)
        response = self.webapp_request(path='/admin', command='set', signal='localhost_1', key='add_disable', value='ui')
        self.assertEqual(len(response.signals['localhost_1']['disables']), 1)
        self.assertIn('ui', response.signals['localhost_1']['disables'])
        response = self.webapp_request(path='/admin', command='set', signal='localhost_1', key='add_disable', value='ui')  # no change allready in list
        self.assertEqual(len(response.signals['localhost_1']['disables']), 1)
        self.assertIn('ui', response.signals['localhost_1']['disables'])
        response = self.webapp_request(path='/admin', command='set', signal='localhost_1', key='add_disable', value='metric')
        self.assertEqual(len(response.signals['localhost_1']['disables']), 2)
        self.assertIn('ui', response.signals['localhost_1']['disables'])
        self.assertIn('metric', response.signals['localhost_1']['disables'])
        response = self.webapp_request(path='/admin', command='set', signal='localhost_1', key='del_disable', value='ui')
        self.assertEqual(len(response.signals['localhost_1']['disables']), 1)
        self.assertIn('metric', response.signals['localhost_1']['disables'])
        response = self.webapp_request(path='/admin', command='set', signal='localhost_1', key='del_disable', value='ui')  # no change allready removed
        self.assertEqual(len(response.signals['localhost_1']['disables']), 1)
        self.assertIn('metric', response.signals['localhost_1']['disables'])
        response = self.webapp_request(path='/admin', command='set', signal='localhost_1', key='del_disable', value='metric')
        self.assertEqual(len(response.signals['localhost_1']['disables']), 0)

    def test_mqtt_messages_are_send(self):
        response = self.webapp_request(clear_state=True, mqtt_test=True, v=self.v, s=3)
        self.assertNotIn('brick/localhost/signal/', response.mqtt)

        response = self.webapp_request(mqtt_test=True, y=['i'])
        self.assertIn('brick/localhost/signal/localhost_0 0', response.mqtt)
        self.assertIn('brick/localhost/signal/localhost_1 0', response.mqtt)
        self.assertIn('brick/localhost/signal/localhost_2 0', response.mqtt)

        response = self.webapp_request(mqtt_test=True, path='/admin', command='set', key='signal', signal='localhost_0', value=1)
        self.assertIn('brick/localhost/signal/localhost_0 11', response.mqtt)
        response = self.webapp_request(mqtt_test=True)
        self.assertIn('brick/localhost/signal/localhost_0 1', response.mqtt)
        self.assertIn('brick/localhost/signal/localhost_1 0', response.mqtt)
        self.assertIn('brick/localhost/signal/localhost_2 0', response.mqtt)

        response = self.webapp_request(mqtt_test=True, path='/admin', command='set', key='signal', signal='localhost_0', value=0)
        self.assertIn('brick/localhost/signal/localhost_0 10', response.mqtt)
        response = self.webapp_request(mqtt_test=True, path='/admin', command='set', key='signal', signal='localhost_1', value=1)
        self.assertIn('brick/localhost/signal/localhost_1 11', response.mqtt)
        response = self.webapp_request(mqtt_test=True)
        self.assertIn('brick/localhost/signal/localhost_0 0', response.mqtt)
        self.assertIn('brick/localhost/signal/localhost_1 1', response.mqtt)
        self.assertIn('brick/localhost/signal/localhost_2 0', response.mqtt)

        # disable signal 1 to send mqtt messages
        response = self.webapp_request(path='/admin', command='set', signal='localhost_1', key='add_disable', value='mqtt')
        response = self.webapp_request(mqtt_test=True, path='/admin', command='set', key='signal', signal='localhost_1', value=1)
        self.assertNotIn('brick/localhost/signal/', response.mqtt)
        response = self.webapp_request(mqtt_test=True)
        self.assertIn('brick/localhost/signal/localhost_0 0', response.mqtt)
        self.assertNotIn('brick/localhost/signal/localhost_1 1', response.mqtt)
        self.assertIn('brick/localhost/signal/localhost_2 0', response.mqtt)

        # reanable signal 1 to send mqtt messages
        response = self.webapp_request(path='/admin', command='set', signal='localhost_1', key='del_disable', value='mqtt')
        response = self.webapp_request(mqtt_test=True, path='/admin', command='set', key='signal', signal='localhost_1', value=1)
        self.assertIn('brick/localhost/signal/localhost_1 11', response.mqtt)
        response = self.webapp_request(mqtt_test=True)
        self.assertIn('brick/localhost/signal/localhost_0 0', response.mqtt)
        self.assertIn('brick/localhost/signal/localhost_1 1', response.mqtt)
        self.assertIn('brick/localhost/signal/localhost_2 0', response.mqtt)
