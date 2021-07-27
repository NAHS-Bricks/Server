from ._wrapper import *
from connector.rabbitmq import wait_for_all_events_done
from helpers.shared import event_worker_is_running

eventsystem_versions = [['os', 1.0], ['all', 1.0]]


class TestEventSystem(BaseCherryPyTestCase):
    def test_add_delete_reorder_events(self):
        response = self.webapp_request(clear_state=True, v=eventsystem_versions)
        self.assertEqual(len(response.state['events']), 0)

        response = self.webapp_request(path='/admin', command='get_event')
        self.assertEqual(response.json['s'], 22)  # event not in data

        response = self.webapp_request(path='/admin', command='get_event', event='invalid')
        self.assertEqual(response.json['s'], 21)  # invalid event

        response = self.webapp_request(path='/admin', command='add_event')
        self.assertEqual(response.json['s'], 11)  # brick missing in data

        response = self.webapp_request(path='/admin', command='add_event', brick='localhost')
        self.assertEqual(len(response.state['events']), 1)

        response = self.webapp_request(path='/admin', command='add_event', brick='localhost')
        self.assertEqual(len(response.state['events']), 2)

        response = self.webapp_request(path='/admin', command='add_event', brick='localhost')
        self.assertEqual(len(response.state['events']), 3)
        response = self.webapp_request(path='/admin', command='get_count', item='events')
        self.assertEqual(response.json['count'], 3)

        response = self.webapp_request(path='/admin', command='add_event', brick='localhost')
        self.assertEqual(len(response.state['events']), 4)

        last_event = response.json['event']['_id']

        response = self.webapp_request(path='/admin', command='delete_event')
        self.assertEqual(response.json['s'], 11)  # brick missing in data

        response = self.webapp_request(path='/admin', command='delete_event', brick='localhost')
        self.assertEqual(response.json['s'], 22)  # event missing in data

        response = self.webapp_request(path='/admin', command='delete_event', brick='localhost', event=last_event)
        self.assertIn('deleted', response.json)
        self.assertIn('event', response.json['deleted'])
        self.assertEqual(response.json['deleted']['event'], last_event)
        self.assertEqual(len(response.state['events']), 3)

        events = response.state['events']
        response = self.webapp_request(path='/admin', command='set', key="pos", value=3)
        self.assertEqual(response.json['s'], 22)  # event is missing

        response = self.webapp_request(path='/admin', command='set', key="pos", event=events[0], value=3)
        self.assertEqual(response.json['s'], 7)  # invalid pos

        response = self.webapp_request(path='/admin', command='set', key="pos", event=events[0], value=-1)
        self.assertEqual(response.json['s'], 7)  # invalid pos
        self.assertEqual(response.state['events'], events)

        response = self.webapp_request(path='/admin', command='set', key="pos", event=events[2], value=0)  # last to first
        events = [events[2], events[0], events[1]]
        self.assertEqual(response.state['events'], events)

        response = self.webapp_request(path='/admin', command='set', key="pos", event=events[0], value=2)  # first to last
        events = [events[1], events[2], events[0]]
        self.assertEqual(response.state['events'], events)

        response = self.webapp_request(path='/admin', command='set', key="pos", event=events[1], value=2)  # middle to last
        events = [events[0], events[2], events[1]]
        self.assertEqual(response.state['events'], events)

        response = self.webapp_request(path='/admin', command='set', key="pos", event=events[1], value=0)  # middle to first
        events = [events[1], events[0], events[2]]
        self.assertEqual(response.state['events'], events)

        response = self.webapp_request(path='/admin', command='set', key="pos", event=events[0], value=1)  # first to middle
        events = [events[1], events[0], events[2]]
        self.assertEqual(response.state['events'], events)

        response = self.webapp_request(path='/admin', command='set', key="pos", event=events[2], value=1)  # last to middle
        events = [events[0], events[2], events[1]]
        self.assertEqual(response.state['events'], events)

    def test_set_event_command(self):
        response = self.webapp_request(clear_state=True, v=eventsystem_versions)
        self.assertEqual(len(response.state['events']), 0)
        response = self.webapp_request(path='/admin', command='add_event', brick='localhost')

        event = response.json['event']
        event_commands = self.webapp_request(path='/admin', command='get_event_commands').json['commands']

        response = self.webapp_request(path='/admin', command='set', key="event_command", value='bullshit')
        self.assertEqual(response.json['s'], 24)  # event_data missing in data

        response = self.webapp_request(path='/admin', command='set', key="event_command", event=event['_id'], event_data='test', value='bullshit')
        self.assertEqual(response.json['s'], 28)  # invalid event_command in value

        response = self.webapp_request(path='/admin', command='set', key="event_command", event=event['_id'], event_data='test', value=event_commands[0])
        event = self.webapp_request(path='/admin', command='get_event', event=event['_id']).json['event']
        self.assertEqual(event['command'], [event_commands[0], 'test'])

        response = self.webapp_request(path='/admin', command='set', key="event_command", event=event['_id'], event_data='test', value=event_commands[1])
        event = self.webapp_request(path='/admin', command='get_event', event=event['_id']).json['event']
        self.assertEqual(event['command'], [event_commands[1], 'test'])

    def test_add_delete_reorder_event_reactions(self):
        response = self.webapp_request(clear_state=True, v=eventsystem_versions)
        self.assertEqual(len(response.state['events']), 0)
        response = self.webapp_request(path='/admin', command='add_event', brick='localhost')

        event = response.json['event']
        event_reactions = self.webapp_request(path='/admin', command='get_event_reactions').json['reactions']

        response = self.webapp_request(path='/admin', command='add_event_reaction', event=event['_id'])
        self.assertEqual(response.json['s'], 24)  # event_data missing in data

        response = self.webapp_request(path='/admin', command='add_event_reaction', event=event['_id'], event_data='test1')
        self.assertEqual(response.json['s'], 25)  # event_reaction is missing in data

        response = self.webapp_request(path='/admin', command='add_event_reaction', event=event['_id'], event_reaction='bullshit', event_data='test1')
        self.assertEqual(response.json['s'], 23)  # invalid event_reaction

        response = self.webapp_request(path='/admin', command='add_event_reaction', event_reaction='bullshit')
        self.assertEqual(response.json['s'], 22)  # event is minnsin in data

        event = self.webapp_request(path='/admin', command='get_event', event=event['_id']).json['event']
        self.assertEqual(len(event['reactions']), 0)
        response = self.webapp_request(path='/admin', command='add_event_reaction', event=event['_id'], event_reaction=event_reactions[0], event_data='test1')
        event = response.json['event']
        self.assertEqual(len(event['reactions']), 1)

        response = self.webapp_request(path='/admin', command='add_event_reaction', event=event['_id'], event_reaction=event_reactions[0], event_data='test2')
        response = self.webapp_request(path='/admin', command='add_event_reaction', event=event['_id'], event_reaction=event_reactions[0], event_data='test3')
        response = self.webapp_request(path='/admin', command='add_event_reaction', event=event['_id'], event_reaction=event_reactions[0], event_data='test4')
        event = response.json['event']
        self.assertEqual(len(event['reactions']), 4)

        response = self.webapp_request(path='/admin', command='delete_event_reaction')
        self.assertEqual(response.json['s'], 22)  # event is missing in data

        response = self.webapp_request(path='/admin', command='delete_event_reaction', event=event['_id'])
        self.assertEqual(response.json['s'], 26)  # pos is missing in data

        response = self.webapp_request(path='/admin', command='delete_event_reaction', event=event['_id'], pos=4)
        self.assertEqual(response.json['s'], 7)  # invalid pos

        response = self.webapp_request(path='/admin', command='delete_event_reaction', event=event['_id'], pos=-1)
        self.assertEqual(response.json['s'], 7)  # invalid pos

        response = self.webapp_request(path='/admin', command='delete_event_reaction', event=event['_id'], pos=3)
        event = response.json['event']
        self.assertEqual(len(event['reactions']), 3)

        response = self.webapp_request(path='/admin', command='set', key='pos', event=event['_id'], reaction_src=-1, value=0)
        self.assertEqual(response.json['s'], 7)  # invalid index for reaction_src
        response = self.webapp_request(path='/admin', command='set', key='pos', event=event['_id'], reaction_src=3, value=0)
        self.assertEqual(response.json['s'], 7)  # invalid index for reaction_src
        response = self.webapp_request(path='/admin', command='set', key='pos', event=event['_id'], reaction_src=0, value=-1)
        self.assertEqual(response.json['s'], 7)  # invalid index for value
        response = self.webapp_request(path='/admin', command='set', key='pos', event=event['_id'], reaction_src=0, value=3)
        self.assertEqual(response.json['s'], 7)  # invalid index for value
        self.assertEqual(event['reactions'][0][1], 'test1')
        self.assertEqual(event['reactions'][1][1], 'test2')
        self.assertEqual(event['reactions'][2][1], 'test3')

        response = self.webapp_request(path='/admin', command='set', key='pos', event=event['_id'], reaction_src=2, value=0)  # last to first
        event = self.webapp_request(path='/admin', command='get_event', event=event['_id']).json['event']
        self.assertEqual(event['reactions'][0][1], 'test3')
        self.assertEqual(event['reactions'][1][1], 'test1')
        self.assertEqual(event['reactions'][2][1], 'test2')

        response = self.webapp_request(path='/admin', command='set', key='pos', event=event['_id'], reaction_src=0, value=2)  # first to last
        event = self.webapp_request(path='/admin', command='get_event', event=event['_id']).json['event']
        self.assertEqual(event['reactions'][0][1], 'test1')
        self.assertEqual(event['reactions'][1][1], 'test2')
        self.assertEqual(event['reactions'][2][1], 'test3')

        response = self.webapp_request(path='/admin', command='set', key='pos', event=event['_id'], reaction_src=1, value=2)  # middle to last
        event = self.webapp_request(path='/admin', command='get_event', event=event['_id']).json['event']
        self.assertEqual(event['reactions'][0][1], 'test1')
        self.assertEqual(event['reactions'][1][1], 'test3')
        self.assertEqual(event['reactions'][2][1], 'test2')

        response = self.webapp_request(path='/admin', command='set', key='pos', event=event['_id'], reaction_src=2, value=1)  # last to middle
        event = self.webapp_request(path='/admin', command='get_event', event=event['_id']).json['event']
        self.assertEqual(event['reactions'][0][1], 'test1')
        self.assertEqual(event['reactions'][1][1], 'test2')
        self.assertEqual(event['reactions'][2][1], 'test3')

        response = self.webapp_request(path='/admin', command='set', key='pos', event=event['_id'], reaction_src=1, value=0)  # middle to first
        event = self.webapp_request(path='/admin', command='get_event', event=event['_id']).json['event']
        self.assertEqual(event['reactions'][0][1], 'test2')
        self.assertEqual(event['reactions'][1][1], 'test1')
        self.assertEqual(event['reactions'][2][1], 'test3')

        response = self.webapp_request(path='/admin', command='set', key='pos', event=event['_id'], reaction_src=0, value=1)  # first to middle
        event = self.webapp_request(path='/admin', command='get_event', event=event['_id']).json['event']
        self.assertEqual(event['reactions'][0][1], 'test1')
        self.assertEqual(event['reactions'][1][1], 'test2')
        self.assertEqual(event['reactions'][2][1], 'test3')

    def test_handling_event_data(self):
        response = self.webapp_request(clear_state=True, v=eventsystem_versions)
        event = self.webapp_request(path='/admin', command='add_event', brick='localhost').json['event']

        response = self.webapp_request(path='/admin', command='get_event_data', event=event['_id'])
        self.assertEqual(response.json['s'], 24)  # event_data is missing in data

        ed = self.webapp_request(path='/admin', command='get_event_data', event=event['_id'], event_data='test').json['event_data']
        self.assertEqual(len(ed.keys()), 1)

        response = self.webapp_request(path='/admin', command='update_event_data', event_data='test')
        self.assertEqual(response.json['s'], 22)  # event is missing in data
        response = self.webapp_request(path='/admin', command='update_event_data', event=event['_id'], content={'t1': 1})
        self.assertEqual(response.json['s'], 24)  # event_data is missing in data
        response = self.webapp_request(path='/admin', command='update_event_data', event=event['_id'], event_data='test')
        self.assertEqual(response.json['s'], 27)  # content is missing in data
        response = self.webapp_request(path='/admin', command='update_event_data', event=event['_id'], event_data='test', content=[])
        self.assertEqual(response.json['s'], 29)  # content needs to be dict

        self.webapp_request(path='/admin', command='update_event_data', event=event['_id'], event_data='test', content={'t1': 1})
        ed = self.webapp_request(path='/admin', command='get_event_data', event=event['_id'], event_data='test').json['event_data']
        self.assertEqual(len(ed.keys()), 2)
        self.assertIn('t1', ed)

        self.webapp_request(path='/admin', command='update_event_data', event=event['_id'], event_data='test', content={'t2': 2})
        ed = self.webapp_request(path='/admin', command='get_event_data', event=event['_id'], event_data='test').json['event_data']
        self.assertEqual(len(ed.keys()), 3)
        self.assertIn('t1', ed)
        self.assertIn('t2', ed)

        response = self.webapp_request(path='/admin', command='replace_event_data', event=event['_id'], content={'t3': 3})
        self.assertEqual(response.json['s'], 24)  # event_data is missing in data
        response = self.webapp_request(path='/admin', command='replace_event_data', event=event['_id'], event_data='test')
        self.assertEqual(response.json['s'], 27)  # content is missing in data
        response = self.webapp_request(path='/admin', command='replace_event_data', event=event['_id'], event_data='test', content=[])
        self.assertEqual(response.json['s'], 29)  # content needs to be dict

        self.webapp_request(path='/admin', command='replace_event_data', event=event['_id'], event_data='test', content={'t3': 3})
        ed = self.webapp_request(path='/admin', command='get_event_data', event=event['_id'], event_data='test').json['event_data']
        self.assertEqual(len(ed.keys()), 2)
        self.assertNotIn('t1', ed)
        self.assertNotIn('t2', ed)
        self.assertIn('t3', ed)

        response = self.webapp_request(path='/admin', command='delete_event_data', event=event['_id'])
        self.assertEqual(response.json['s'], 24)  # event_data is missing in data

        self.webapp_request(path='/admin', command='delete_event_data', event=event['_id'], event_data='test')
        ed = self.webapp_request(path='/admin', command='get_event_data', event=event['_id'], event_data='test').json['event_data']
        self.assertEqual(len(ed.keys()), 1)
        self.assertNotIn('t1', ed)
        self.assertNotIn('t2', ed)
        self.assertNotIn('t3', ed)

    def test_delete_event_with_event_data(self):
        response = self.webapp_request(clear_state=True, v=eventsystem_versions)
        ev1 = self.webapp_request(path='/admin', command='add_event', brick='localhost').json['event']['_id']
        self.webapp_request(path='/admin', command='replace_event_data', brick='localhost', event=ev1, event_data='local', content={})
        ev2 = self.webapp_request(path='/admin', command='add_event', brick='localhost').json['event']['_id']
        self.webapp_request(path='/admin', command='replace_event_data', brick='localhost', event=ev2, event_data='local', content={})
        self.webapp_request(path='/admin', command='replace_event_data', brick='localhost', event=ev2, event_data='_brick', content={})

        response = self.webapp_request(path='/admin', command='get_count', item='event_data')
        self.assertEqual(response.json['count'], 3)
        response = self.webapp_request(path='/admin', command='get_count', item='events')
        self.assertEqual(response.json['count'], 2)

        self.webapp_request(path='/admin', command='delete_event', brick='localhost', event=ev1)

        response = self.webapp_request(path='/admin', command='get_count', item='event_data')
        self.assertEqual(response.json['count'], 2)
        response = self.webapp_request(path='/admin', command='get_count', item='events')
        self.assertEqual(response.json['count'], 1)

        self.webapp_request(path='/admin', command='delete_event', brick='localhost', event=ev2)

        response = self.webapp_request(path='/admin', command='get_count', item='event_data')
        self.assertEqual(response.json['count'], 1)  # brick-level event_data should not have been deleted
        response = self.webapp_request(path='/admin', command='get_count', item='events')
        self.assertEqual(response.json['count'], 0)

    def test_delete_brick_with_events(self):
        response = self.webapp_request(clear_state=True, v=eventsystem_versions)
        event_id = self.webapp_request(path='/admin', command='add_event', brick='localhost').json['event']['_id']
        self.webapp_request(path='/admin', command='replace_event_data', brick='localhost', event=event_id, event_data='_brick', content={})
        event_id = self.webapp_request(path='/admin', command='add_event', brick='localhost').json['event']['_id']
        self.webapp_request(path='/admin', command='replace_event_data', brick='localhost', event=event_id, event_data='local', content={})
        event_id = self.webapp_request(path='/admin', command='add_event', brick='localhost').json['event']['_id']
        self.webapp_request(path='/admin', command='replace_event_data', brick='localhost', event=event_id, event_data='local', content={})

        response = self.webapp_request(path='/admin', command='get_count', item='event_data')
        self.assertEqual(response.json['count'], 3)
        response = self.webapp_request(path='/admin', command='get_count', item='events')
        self.assertEqual(response.json['count'], 3)
        response = self.webapp_request(path='/admin', command='get_count', item='bricks')
        self.assertEqual(response.json['count'], 1)

        self.webapp_request(path='/admin', command='delete_brick', brick='localhost')

        response = self.webapp_request(path='/admin', command='get_count', item='events')
        self.assertEqual(response.json['count'], 0)
        response = self.webapp_request(path='/admin', command='get_count', item='bricks')
        self.assertEqual(response.json['count'], 0)
        response = self.webapp_request(path='/admin', command='get_count', item='event_data')
        self.assertEqual(response.json['count'], 0)

        # special case brick with only brick-level event_data
        response = self.webapp_request(clear_state=True, v=eventsystem_versions)
        event_id = self.webapp_request(path='/admin', command='add_event', brick='localhost').json['event']['_id']
        self.webapp_request(path='/admin', command='replace_event_data', brick='localhost', event=event_id, event_data='_brick', content={})

        response = self.webapp_request(path='/admin', command='get_count', item='event_data')
        self.assertEqual(response.json['count'], 1)
        response = self.webapp_request(path='/admin', command='get_count', item='events')
        self.assertEqual(response.json['count'], 1)
        response = self.webapp_request(path='/admin', command='get_count', item='bricks')
        self.assertEqual(response.json['count'], 1)

        self.webapp_request(path='/admin', command='delete_brick', brick='localhost')

        response = self.webapp_request(path='/admin', command='get_count', item='events')
        self.assertEqual(response.json['count'], 0)
        response = self.webapp_request(path='/admin', command='get_count', item='bricks')
        self.assertEqual(response.json['count'], 0)
        response = self.webapp_request(path='/admin', command='get_count', item='event_data')
        self.assertEqual(response.json['count'], 0)

    def test_event_data_scopes(self):
        response = self.webapp_request(clear_state=True, v=eventsystem_versions)
        response = self.webapp_request(test_brick_id=1, v=eventsystem_versions)
        b1e1 = self.webapp_request(path='/admin', command='add_event', brick='localhost').json['event']['_id']
        b1e2 = self.webapp_request(path='/admin', command='add_event', brick='localhost').json['event']['_id']
        b2e1 = self.webapp_request(path='/admin', command='add_event', brick='localhost1').json['event']['_id']
        b2e2 = self.webapp_request(path='/admin', command='add_event', brick='localhost1').json['event']['_id']

        # local scope: nothing is equal
        self.webapp_request(path='/admin', command='replace_event_data', brick='localhost', event=b1e1, event_data='local', content={'c': 'b1e1'})
        self.webapp_request(path='/admin', command='replace_event_data', brick='localhost', event=b1e2, event_data='local', content={'c': 'b1e2'})
        self.webapp_request(path='/admin', command='replace_event_data', brick='localhost1', event=b2e1, event_data='local', content={'c': 'b2e1'})
        self.webapp_request(path='/admin', command='replace_event_data', brick='localhost1', event=b2e2, event_data='local', content={'c': 'b2e2'})
        ed_b1e1 = self.webapp_request(path='/admin', command='get_event_data', brick='localhost', event=b1e1, event_data='local').json['event_data']['c']
        ed_b1e2 = self.webapp_request(path='/admin', command='get_event_data', brick='localhost', event=b1e2, event_data='local').json['event_data']['c']
        ed_b2e1 = self.webapp_request(path='/admin', command='get_event_data', brick='localhost1', event=b2e1, event_data='local').json['event_data']['c']
        ed_b2e2 = self.webapp_request(path='/admin', command='get_event_data', brick='localhost1', event=b2e2, event_data='local').json['event_data']['c']
        self.assertNotEqual(ed_b1e1, ed_b1e2)
        self.assertNotEqual(ed_b2e1, ed_b2e2)
        self.assertNotEqual(ed_b1e1, ed_b2e1)

        # brick scope: equal on same brick but not on different brick
        self.webapp_request(path='/admin', command='replace_event_data', brick='localhost', event=b1e1, event_data='_brick', content={'c': 'b1e1'})
        self.webapp_request(path='/admin', command='replace_event_data', brick='localhost', event=b1e2, event_data='_brick', content={'c': 'b1e2'})
        self.webapp_request(path='/admin', command='replace_event_data', brick='localhost1', event=b2e1, event_data='_brick', content={'c': 'b2e1'})
        self.webapp_request(path='/admin', command='replace_event_data', brick='localhost1', event=b2e2, event_data='_brick', content={'c': 'b2e2'})
        ed_b1e1 = self.webapp_request(path='/admin', command='get_event_data', brick='localhost', event=b1e1, event_data='_brick').json['event_data']['c']
        ed_b1e2 = self.webapp_request(path='/admin', command='get_event_data', brick='localhost', event=b1e2, event_data='_brick').json['event_data']['c']
        ed_b2e1 = self.webapp_request(path='/admin', command='get_event_data', brick='localhost1', event=b2e1, event_data='_brick').json['event_data']['c']
        ed_b2e2 = self.webapp_request(path='/admin', command='get_event_data', brick='localhost1', event=b2e2, event_data='_brick').json['event_data']['c']
        self.assertEqual(ed_b1e1, ed_b1e2)
        self.assertEqual(ed_b2e1, ed_b2e2)
        self.assertNotEqual(ed_b1e1, ed_b2e1)

        # global scope: everything is equal
        self.webapp_request(path='/admin', command='replace_event_data', brick='localhost', event=b1e1, event_data='__global', content={'c': 'b1e1'})
        self.webapp_request(path='/admin', command='replace_event_data', brick='localhost', event=b1e2, event_data='__global', content={'c': 'b1e2'})
        self.webapp_request(path='/admin', command='replace_event_data', brick='localhost1', event=b2e1, event_data='__global', content={'c': 'b2e1'})
        self.webapp_request(path='/admin', command='replace_event_data', brick='localhost1', event=b2e2, event_data='__global', content={'c': 'b2e2'})
        ed_b1e1 = self.webapp_request(path='/admin', command='get_event_data', brick='localhost', event=b1e1, event_data='__global').json['event_data']['c']
        ed_b1e2 = self.webapp_request(path='/admin', command='get_event_data', brick='localhost', event=b1e2, event_data='__global').json['event_data']['c']
        ed_b2e1 = self.webapp_request(path='/admin', command='get_event_data', brick='localhost1', event=b2e1, event_data='__global').json['event_data']['c']
        ed_b2e2 = self.webapp_request(path='/admin', command='get_event_data', brick='localhost1', event=b2e2, event_data='__global').json['event_data']['c']
        self.assertEqual(ed_b1e1, ed_b1e2)
        self.assertEqual(ed_b2e1, ed_b2e2)
        self.assertEqual(ed_b1e1, ed_b2e1)

    def test_push_to_event_queue(self):
        response = self.webapp_request(clear_state=True, v=[['os', 1.0], ['all', 1.0], ['latch', 1.0]], l=[0])
        response = self.webapp_request(test_brick_id=1, v=[['os', 1.0], ['all', 1.0], ['signal', 1.0]], s=1)
        response = self.webapp_request(test_brick_id=1)  # bring signals into deliverd state

        b0e = self.webapp_request(path='/admin', command='add_event', brick='localhost').json['event']['_id']
        b1e = self.webapp_request(path='/admin', command='add_event', brick='localhost1').json['event']['_id']
        # this one is the variable, that is counted up
        self.webapp_request(path='/admin', command='replace_event_data', event=b0e, event_data='__counter', content={'val': 0})
        # and this is the event_data for a math reaction to count the __counter up
        self.webapp_request(path='/admin', command='replace_event_data', event=b0e, event_data='__count', content={'operator': '+', 'operand': 1, 'event_data_name': '__counter', 'event_data_key': 'val'})
        # this is b0e command event_data to trigger on latch0 to be 1
        self.webapp_request(path='/admin', command='replace_event_data', event=b0e, event_data='command', content={'expression': ['0', '==', 1]})
        # set b0e's command
        self.webapp_request(path='/admin', command='set', key='event_command', event=b0e, event_data='command', value='latch_state_match')
        # set b0e's reaction
        self.webapp_request(path='/admin', command='add_event_reaction', event=b0e, event_reaction='math', event_data='__count')

        # test event is pushed to queue by a brick deliver
        self.webapp_request(l=[1])  # latch state triggered, val should be one up
        wait_for_all_events_done()
        self.assertEqual(self.webapp_request(path='/admin', command='get_event_data', event=b0e, event_data='__counter').json['event_data']['val'], 1)
        self.webapp_request(l=[0])  # latch state did not trigger, val should stay at level
        wait_for_all_events_done()
        self.assertEqual(self.webapp_request(path='/admin', command='get_event_data', event=b0e, event_data='__counter').json['event_data']['val'], 1)
        self.webapp_request(l=[1])  # latch state triggered again, val should be one up
        wait_for_all_events_done()
        self.assertEqual(self.webapp_request(path='/admin', command='get_event_data', event=b0e, event_data='__counter').json['event_data']['val'], 2)

        # # following configuration is on second brick to receive a signal change via API by event of first brick
        # set the event command, event_data is not used in this case, can be anything (even an empty event_data)
        self.webapp_request(path='/admin', command='set', key='event_command', event=b1e, event_data='command', value='signals_pending')
        # and attach the same event_reaction to this one, to use the same counter (it's global)
        self.webapp_request(path='/admin', command='add_event_reaction', event=b1e, event_reaction='math', event_data='__count')
        # now we need the connection between the two bricks, configure the event_reactions event_data to set the signal
        self.webapp_request(path='/admin', command='replace_event_data', event=b0e, event_data='signal', content={'signal_id': 'localhost1_0', 'state': 1})
        # and attach the reaction to first brick
        self.webapp_request(path='/admin', command='add_event_reaction', event=b0e, event_reaction='set_signal_state', event_data='signal')

        # test if both events trigger one by brick deliver the other by admin interface set indirect
        self.webapp_request(l=[1])  # latch state triggered, val should be two up (one by each event)
        wait_for_all_events_done()
        self.assertEqual(self.webapp_request(path='/admin', command='get_event_data', event=b0e, event_data='__counter').json['event_data']['val'], 4)
        self.webapp_request(l=[0])  # latch state did not trigger, val should stay at level
        wait_for_all_events_done()
        self.assertEqual(self.webapp_request(path='/admin', command='get_event_data', event=b0e, event_data='__counter').json['event_data']['val'], 4)
        self.webapp_request(l=[1])  # latch state triggered again, val should be one up (just by deliver as the reaction to set signal state detects, that signal allready in desired state)
        wait_for_all_events_done()
        self.assertEqual(self.webapp_request(path='/admin', command='get_event_data', event=b0e, event_data='__counter').json['event_data']['val'], 5)

    def test_get_event_data_names(self):
        response = self.webapp_request(clear_state=True, v=eventsystem_versions)
        ev1 = self.webapp_request(path='/admin', command='add_event', brick='localhost').json['event']['_id']
        self.webapp_request(path='/admin', command='replace_event_data', brick='localhost', event=ev1, event_data='_brick1', content={})
        self.webapp_request(path='/admin', command='replace_event_data', brick='localhost', event=ev1, event_data='_brick2', content={})
        self.webapp_request(path='/admin', command='replace_event_data', brick='localhost', event=ev1, event_data='local1', content={})
        self.webapp_request(path='/admin', command='replace_event_data', brick='localhost', event=ev1, event_data='__global1', content={})
        ev2 = self.webapp_request(path='/admin', command='add_event', brick='localhost').json['event']['_id']
        self.webapp_request(path='/admin', command='replace_event_data', brick='localhost', event=ev2, event_data='local2', content={})
        self.webapp_request(path='/admin', command='replace_event_data', brick='localhost', event=ev2, event_data='local3', content={})
        self.webapp_request(path='/admin', command='replace_event_data', brick='localhost', event=ev2, event_data='__global2', content={})

        response = self.webapp_request(path="/admin", command='get_event_data_names', level='bullshit')  # invalid level
        self.assertEqual(response.json['s'], 31)

        response = self.webapp_request(path="/admin", command='get_event_data_names', level='g')
        self.assertEqual(response.json['event_data_names'], ['global1', 'global2'])

        response = self.webapp_request(path="/admin", command='get_event_data_names', event=ev1, level='b')
        self.assertEqual(response.json['event_data_names'], ['brick1', 'brick2'])

        response = self.webapp_request(path="/admin", command='get_event_data_names', event=ev2, level='b')
        self.assertEqual(response.json['event_data_names'], ['brick1', 'brick2'])

        response = self.webapp_request(path="/admin", command='get_event_data_names', event=ev1, level='l')
        self.assertEqual(response.json['event_data_names'], ['local1'])

        response = self.webapp_request(path="/admin", command='get_event_data_names', event=ev2, level='l')
        self.assertEqual(response.json['event_data_names'], ['local2', 'local3'])
