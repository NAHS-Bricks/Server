from ._wrapper import *


@parameterized_class(getVersionParameter('os', minVersion={'os': 1.01}))
class TestFeatureOsV2(BaseCherryPyTestCase):
    def test_sketchMD5_is_saved(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        self.assertIsNone(response.state['sketchMD5'])

        response = self.webapp_request(m='1234')
        self.assertEqual(response.state['sketchMD5'], '1234')

    def test_sketchMD5_is_requested(self):
        # request from None sketchMD5
        response = self.webapp_request(clear_state=True, v=self.v, y=['i'])  # should not be reqested as init is active
        if 'r' in response.json:
            self.assertNotIn(11, response.json['r'])

        response = self.webapp_request()  # should now be requested as sketchMD5 is None and init is not active
        self.assertIn(11, response.json['r'])

        response = self.webapp_request(m='1234')  # should not be reqested as sketchMD5 is set
        if 'r' in response.json:
            self.assertNotIn(11, response.json['r'])

        # request after init
        response = self.webapp_request(y=['i'])  # should not be reqested as init is active
        if 'r' in response.json:
            self.assertNotIn(11, response.json['r'])

        response = self.webapp_request()  # should now be requested as sketchMD5 is None and init is not active
        self.assertIn(11, response.json['r'])

        response = self.webapp_request()  # should be requested again as sketchMD5 is still None and init is not active
        self.assertIn(11, response.json['r'])

        response = self.webapp_request(m='1234')  # should not be reqested as sketchMD5 is set
        if 'r' in response.json:
            self.assertNotIn(11, response.json['r'])

    def test_otaUpdate_is_requested(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        if 'r' in response.json:
            self.assertNotIn(12, response.json['r'])

        self.webapp_request(path='/admin', brick='localhost', command='set', key='otaupdate', value='requested')
        response = self.webapp_request()  # should now be requested
        self.assertEqual(response.state['otaUpdate'], 'requested')
        self.assertIn(12, response.json['r'])

        response = self.webapp_request()  # should keep beeing requested till canceled or otaUpdate is executed
        self.assertEqual(response.state['otaUpdate'], 'requested')
        self.assertIn(12, response.json['r'])

        response = self.webapp_request()  # should keep beeing requested till canceled or otaUpdate is executed
        self.assertEqual(response.state['otaUpdate'], 'requested')
        self.assertIn(12, response.json['r'])

        self.webapp_request(path='/admin', brick='localhost', command='set', key='otaupdate', value='canceled')
        response = self.webapp_request()  # should now be canceled
        if 'r' in response.json:
            self.assertNotIn(12, response.json['r'])

    def test_state_changes_of_otaUpdate(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        self.assertNotIn('otaUpdate', response.state)

        self.webapp_request(path='/admin', brick='localhost', command='set', key='otaupdate', value='requested')
        response = self.webapp_request()
        self.assertEqual(response.state['otaUpdate'], 'requested')

        response = self.webapp_request(path='/ota')
        self.assertEqual(response.state['otaUpdate'], 'skipped')

        response = self.webapp_request(y=['i'])
        self.assertEqual(response.state['otaUpdate'], 'done')

        response = self.webapp_request()
        self.assertNotIn('otaUpdate', response.state)

    def test_otaupdate_admin_interface(self):
        response = self.webapp_request(clear_state=True, v=self.v)

        # value requested is vaild
        response = self.webapp_request(path='/admin', brick='localhost', command='set', key='otaupdate', value='requested')
        self.assertEqual(response.json['s'], 0)

        # value canceled is vaild
        response = self.webapp_request(path='/admin', brick='localhost', command='set', key='otaupdate', value='canceled')
        self.assertEqual(response.json['s'], 0)

        # other values are invalid
        response = self.webapp_request(path='/admin', brick='localhost', command='set', key='otaupdate', value='request')
        self.assertEqual(response.json['s'], 7)
        response = self.webapp_request(path='/admin', brick='localhost', command='set', key='otaupdate', value='cancel')
        self.assertEqual(response.json['s'], 7)

    def test_ident_is_stored(self):
        response = self.webapp_request(clear_state=True, v=self.v)
        if 'r' in response.json:
            self.assertNotIn(14, response.json['r'])
        self.assertIsNone(response.state['desc'])

        # now transmit an ident, this should be stored and the brick should be requested to clear the ident
        response = self.webapp_request(id='somebrickonthewall')
        self.assertIn('r', response.json)
        self.assertIn(14, response.json['r'])
        self.assertEqual(response.state['desc'], 'somebrickonthewall')

        # now transmit an ident again, the description should not change, but again a request to clear the ident is send
        response = self.webapp_request(id='somethingidontwant')
        self.assertIn('r', response.json)
        self.assertIn(14, response.json['r'])
        self.assertEqual(response.state['desc'], 'somebrickonthewall')

        # do not send an ident, no request should be send, also the desc stays as is
        response = self.webapp_request()
        if 'r' in response.json:
            self.assertNotIn(14, response.json['r'])
        self.assertEqual(response.state['desc'], 'somebrickonthewall')


@parameterized_class(getVersionParameter('os', specificVersion=[['os', 1.00]]))
class TestFeatureOsV1(BaseCherryPyTestCase):
    def test_otaupdate_admin_interface(self):
        response = self.webapp_request(clear_state=True, v=self.v)

        # version of os is not satisfied
        response = self.webapp_request(path='/admin', brick='localhost', command='set', key='otaupdate', value='requested')
        self.assertEqual(response.json['s'], 35)