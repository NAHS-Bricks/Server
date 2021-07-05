from ._wrapper import *


@parameterized_class(getVersionParameter('all'))
class TestFeatureAll(BaseCherryPyTestCase):
    def test_new_brick_without_init(self):
        # Newly created brick without any info
        response = self.webapp_request(clear_state=True)
        self.assertNotIn('r', response.json)

        self.assertIn('os', response.state['features'])
        self.assertEqual(response.state['features']['os'], 0)
        self.assertIn('all', response.state['features'])
        self.assertEqual(response.state['features']['all'], 0)
        self.assertIn('type', response.state)
        self.assertEqual(response.state['type'], None)

    def test_new_brick_without_init_but_versions(self):
        # Newly created brick without information, that it is initalized but with version info present
        response = self.webapp_request(clear_state=True, v=self.v)
        if 'temp' not in response.state['features'] and 'bat' not in response.state['features'] and 'signal' not in response.state['features']:
            self.assertNotIn('r', response.json)

        self.assertIn('os', response.state['features'])
        self.assertEqual(response.state['features']['os'], 1)
        self.assertIn('all', response.state['features'])
        self.assertEqual(response.state['features']['all'], 1)
        self.assertIn('type', response.state)
        self.assertEqual(response.state['type'], None)

    def test_new_brick_without_init_but_bricktype(self):
        # Newly created brick without information, that it is initalized but with bricktype present
        response = self.webapp_request(clear_state=True, x=1)
        self.assertNotIn('r', response.json)

        self.assertIn('os', response.state['features'])
        self.assertEqual(response.state['features']['os'], 0)
        self.assertIn('all', response.state['features'])
        self.assertEqual(response.state['features']['all'], 0)
        self.assertIn('type', response.state)
        self.assertEqual(response.state['type'], 1)

    def test_new_brick_without_init_but_versions_and_bricktype(self):
        # Newly created brick without information, that it is initalized but with version info and bricktype present
        response = self.webapp_request(clear_state=True, v=self.v, x=1)
        if 'temp' not in response.state['features'] and 'bat' not in response.state['features'] and 'signal' not in response.state['features']:
            self.assertNotIn('r', response.json)

        self.assertIn('os', response.state['features'])
        self.assertEqual(response.state['features']['os'], 1)
        self.assertIn('all', response.state['features'])
        self.assertEqual(response.state['features']['all'], 1)
        self.assertIn('type', response.state)
        self.assertEqual(response.state['type'], 1)

    def test_new_brick_with_init(self):
        # Newly created brick is initilized, without version info or bricktype present
        response = self.webapp_request(clear_state=True, y=['i'])
        self.assertIn('r', response.json)
        self.assertEqual(len(response.json['r']), 2)
        self.assertIn(1, response.json['r'])
        self.assertIn(5, response.json['r'])

        self.assertIn('os', response.state['features'])
        self.assertEqual(response.state['features']['os'], 0)
        self.assertIn('all', response.state['features'])
        self.assertEqual(response.state['features']['all'], 0)
        self.assertIn('type', response.state)
        self.assertEqual(response.state['type'], None)

    def test_new_brick_with_init_and_versions(self):
        # Newly created brick is initilized, with version info but without bricktype present
        response = self.webapp_request(clear_state=True, y=['i'], v=self.v)
        self.assertIn('r', response.json)
        self.assertIn(1, response.json['r'])
        self.assertIn(5, response.json['r'])

        self.assertIn('os', response.state['features'])
        self.assertEqual(response.state['features']['os'], 1)
        self.assertIn('all', response.state['features'])
        self.assertEqual(response.state['features']['all'], 1)
        self.assertIn('type', response.state)
        self.assertEqual(response.state['type'], None)

    def test_new_brick_with_init_and_bricktype(self):
        # Newly created brick is initilized, with bricktype but without version info present
        response = self.webapp_request(clear_state=True, y=['i'], x=1)
        self.assertIn('r', response.json)
        self.assertIn(1, response.json['r'])
        self.assertIn(5, response.json['r'])

        self.assertIn('os', response.state['features'])
        self.assertEqual(response.state['features']['os'], 0)
        self.assertIn('all', response.state['features'])
        self.assertEqual(response.state['features']['all'], 0)
        self.assertIn('type', response.state)
        self.assertEqual(response.state['type'], 1)

    def test_new_brick_with_init_and_versions_and_bricktype(self):
        # Newly created brick is initilized, with version info and bricktype present
        response = self.webapp_request(clear_state=True, y=['i'], v=self.v, x=1)
        self.assertIn('r', response.json)
        self.assertIn(1, response.json['r'])
        self.assertIn(5, response.json['r'])

        self.assertIn('os', response.state['features'])
        self.assertEqual(response.state['features']['os'], 1)
        self.assertIn('all', response.state['features'])
        self.assertEqual(response.state['features']['all'], 1)
        self.assertIn('type', response.state)
        self.assertEqual(response.state['type'], 1)


class TestFeatureAllStaticFeatures(BaseCherryPyTestCase):
    def test_adding_feature(self):  # a brick migth change over time
        response = self.webapp_request(clear_state=True, v=[['all', 1.0], ['os', 1.0]])
        self.assertEqual(len(response.state['features']), 2)
        self.assertIn('all', response.state['features'])
        self.assertIn('os', response.state['features'])

        response = self.webapp_request(v=[['all', '1.0'], ['os', 1.0], ['sleep', 1.0]])  # add a new feature without deleting brick beforehand
        self.assertEqual(len(response.state['features']), 3)
        self.assertIn('all', response.state['features'])
        self.assertIn('os', response.state['features'])
        self.assertIn('sleep', response.state['features'])

    def test_deleting_feature(self):  # a brick migth change over time
        response = self.webapp_request(clear_state=True, v=[['all', 1.0], ['os', 1.0], ['sleep', 1.0]])
        self.assertEqual(len(response.state['features']), 3)
        self.assertIn('all', response.state['features'])
        self.assertIn('os', response.state['features'])
        self.assertIn('sleep', response.state['features'])

        response = self.webapp_request(v=[['all', '1.0'], ['os', 1.0]])  # delete a feature without deleting brick beforehand
        self.assertEqual(len(response.state['features']), 2)
        self.assertIn('all', response.state['features'])
        self.assertIn('os', response.state['features'])

    def test_add_and_delete_feature_at_once(self):  # a brick migth change over time
        response = self.webapp_request(clear_state=True, v=[['all', 1.0], ['os', 1.0], ['sleep', 1.0]])
        self.assertEqual(len(response.state['features']), 3)
        self.assertIn('all', response.state['features'])
        self.assertIn('os', response.state['features'])
        self.assertIn('sleep', response.state['features'])

        response = self.webapp_request(v=[['all', 1.0], ['os', 1.0], ['bat', 1.0]])  # delete sleep and add bat
        self.assertEqual(len(response.state['features']), 3)
        self.assertIn('all', response.state['features'])
        self.assertIn('os', response.state['features'])
        self.assertIn('bat', response.state['features'])
        self.assertNotIn('sleep', response.state['features'])

    def test_multiple_testing_bricks_are_generated(self):  # there are cases whre it is nesseccary to test on/with multiple bricks, so test if this is possible
        response = self.webapp_request(clear_state=True, v=[['all', 1.0], ['os', 1.0]])
        self.assertEqual(self.webapp_request(path='/admin', command='get_count', item='bricks').json['count'], 1)

        response = self.webapp_request(test_brick_id=1, v=[['all', 1.0], ['os', 1.0], ['sleep', 1.0]])
        self.assertEqual(self.webapp_request(path='/admin', command='get_count', item='bricks').json['count'], 2)

        self.webapp_request(path='/admin', command='set', key='desc', brick='localhost', value='brickdesc0')
        self.webapp_request(path='/admin', command='set', key='desc', brick='localhost1', value='brickdesc1')

        # are the object independent?
        brick = self.webapp_request(path='/admin', command='get_brick', brick='localhost').json['brick']
        self.assertEqual(brick['desc'], 'brickdesc0')
        self.assertEqual(len(brick['features']), 2)
        brick = self.webapp_request(path='/admin', command='get_brick', brick='localhost1').json['brick']
        self.assertEqual(brick['desc'], 'brickdesc1')
        self.assertEqual(len(brick['features']), 3)

        # generate one more
        response = self.webapp_request(test_brick_id=2, v=[['all', 1.0], ['os', 1.0]])
        self.assertEqual(self.webapp_request(path='/admin', command='get_count', item='bricks').json['count'], 3)

        # delete it
        self.webapp_request(path='/admin', command='delete_brick', brick='localhost2')
        self.assertEqual(self.webapp_request(path='/admin', command='get_count', item='bricks').json['count'], 2)

        # and test if clearing also clears all bricks
        response = self.webapp_request(clear_state=True, v=[['all', 1.0], ['os', 1.0]])
        self.assertEqual(self.webapp_request(path='/admin', command='get_count', item='bricks').json['count'], 1)
