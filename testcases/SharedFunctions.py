from ._wrapper import *
from helpers.shared import version_less_than, version_greater_or_equal_than


class TestSharedFunctions(BaseCherryPyTestCase):
    def test_version_less_than(self):
        self.assertTrue(version_less_than('1.0', '1.0.1'))
        #self.assertTrue(version_less_than('1.0.0.1', '1.0.0.2'))
        self.assertFalse(version_less_than('1.0', '1.0'))
        self.assertFalse(version_less_than('1.0.1', '1.0'))

    def test_version_greater_or_equal_than(self):
        self.assertFalse(version_greater_or_equal_than('1.0', '1.0.1'))
        self.assertTrue(version_greater_or_equal_than('1.0', '1.0'))
        self.assertTrue(version_greater_or_equal_than('1.0.1', '1.0'))
