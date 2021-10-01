from ._wrapper import *
from connector.brick import activate as brick_activate
import json


@parameterized_class(getVersionParameter('all', ['sleep']))
class TestConnectorBrick(BaseCherryPyTestCase):
    def test_direct_activation(self):
        response = self.webapp_request(clear_state=True, v=self.v)

        # activate by brick-object
        self.start_activator_test()
        brick_activate(response.state)
        result = self.end_activator_test()
        self.assertIn('localhost', result)

        # no activation should not activate brick
        self.start_activator_test()
        result = self.end_activator_test()
        self.assertNotIn('localhost', result)

        # activate by brick-id
        self.start_activator_test()
        brick_activate(brick_id='localhost')
        result = self.end_activator_test()
        self.assertIn('localhost', result)

    def test_activation_via_admin_flag(self):
        response = self.webapp_request(clear_state=True, v=self.v)

        # sending activation flag
        self.start_activator_test()
        self.webapp_request('/admin', command='set', brick='localhost', key='desc', value='test', activate=True)
        result = self.end_activator_test()
        self.assertIn('localhost', result)

        # not sending activation flag
        self.start_activator_test()
        self.webapp_request('/admin', command='set', brick='localhost', key='desc', value='test')
        result = self.end_activator_test()
        self.assertNotIn('localhost', result)

        # special case -- all delay transmissions should be poped by activator
        self.start_activator_test()
        self.webapp_request('/admin', command='set', brick='localhost', key='delay', value=33, activate=True)
        result = self.end_activator_test()
        self.assertIn('localhost', result)
        for line in result.strip().split('\n'):
            if line.startswith('localhost'):
                line_feedback = json.loads(line.replace('localhost=', ''))
                self.assertNotIn('d', line_feedback)


@parameterized_class(getVersionParameter(['all', 'sleep'], minVersion={'sleep': 1.01}))
class TestConnectorBrickWithSleep(BaseCherryPyTestCase):
    def test_direct_activation(self):
        response = self.webapp_request(clear_state=True, v=self.v)

        # sleep enabled, should not try to activate brick
        self.start_activator_test()
        brick_activate(response.state)
        result = self.end_activator_test()
        self.assertNotIn('localhost', result)

        response = self.webapp_request(y=['q'])

        # sleep disabled, should try to activate brick
        self.start_activator_test()
        brick_activate(response.state)
        result = self.end_activator_test()
        self.assertIn('localhost', result)

    def test_activation_via_admin_flag(self):
        response = self.webapp_request(clear_state=True, v=self.v, y=['q'])

        # sending activation flag
        self.start_activator_test()
        self.webapp_request('/admin', command='set', brick='localhost', key='desc', value='test', activate=True)
        result = self.end_activator_test()
        self.assertIn('localhost', result)

        # not sending activation flag
        self.start_activator_test()
        self.webapp_request('/admin', command='set', brick='localhost', key='desc', value='test')
        result = self.end_activator_test()
        self.assertNotIn('localhost', result)

        response = self.webapp_request()

        # sending activation flag with enabled sleeping should not activate brick
        self.start_activator_test()
        self.webapp_request('/admin', command='set', brick='localhost', key='desc', value='test', activate=True)
        result = self.end_activator_test()
        self.assertNotIn('localhost', result)
