from ._wrapper import *
from helpers.shared import version_less_than, version_greater_or_equal_than, calculate_bat_prediction
from datetime import datetime


class TestSharedFunctions(BaseCherryPyTestCase):
    def test_version_less_than(self):
        self.assertTrue(version_less_than('1.0', '1.0.1'))
        self.assertTrue(version_less_than('1.0.0.1', '1.0.0.2'))
        self.assertFalse(version_less_than('1.0', '1.0'))
        self.assertFalse(version_less_than('1.0.1', '1.0'))

    def test_version_greater_or_equal_than(self):
        self.assertFalse(version_greater_or_equal_than('1.0', '1.0.1'))
        self.assertTrue(version_greater_or_equal_than('1.0', '1.0'))
        self.assertTrue(version_greater_or_equal_than('1.0.1', '1.0'))

    def test_calculate_bat_prediction(self):
        # ATTENTION: these tests might change with bat_prediction_reference.dat
        dti = int(datetime.strptime("2021-03-17T10:39:57Z", "%Y-%m-%dT%H:%M:%SZ").timestamp())
        ri = 3.9217
        dtl = int(datetime.strptime("2021-03-25T13:06:45Z", "%Y-%m-%dT%H:%M:%SZ").timestamp())
        rl = 3.7929
        self.assertEqual(int(calculate_bat_prediction(None, dti, ri, dtl, rl)), 41)

        dti = int(datetime.strptime("2021-04-15T10:55:08Z", "%Y-%m-%dT%H:%M:%SZ").timestamp())
        ri = 3.9802
        dtl = int(datetime.strptime("2021-04-22T11:58:57Z", "%Y-%m-%dT%H:%M:%SZ").timestamp())
        rl = 3.7762
        self.assertEqual(int(calculate_bat_prediction(None, dti, ri, dtl, rl)), 21)

        dti = int(datetime.strptime("2021-05-10T03:03:46Z", "%Y-%m-%dT%H:%M:%SZ").timestamp())
        ri = 4.0558
        dtl = int(datetime.strptime("2021-05-31T17:27:48Z", "%Y-%m-%dT%H:%M:%SZ").timestamp())
        rl = 3.7393
        self.assertEqual(int(calculate_bat_prediction(None, dti, ri, dtl, rl)), 38)

        # Edge-Case: ri and rl really close together, where ri is over first ref-date
        dti = int(datetime.strptime("2021-05-10T03:03:46Z", "%Y-%m-%dT%H:%M:%SZ").timestamp())
        ri = 4.304252
        dtl = int(datetime.strptime("2021-05-11T17:27:48Z", "%Y-%m-%dT%H:%M:%SZ").timestamp())
        rl = 4.304251
        self.assertEqual(int(calculate_bat_prediction(None, dti, ri, dtl, rl)), 255)

        # Edge-Case: rl under last ref-date
        dti = int(datetime.strptime("2021-05-10T03:03:46Z", "%Y-%m-%dT%H:%M:%SZ").timestamp())
        ri = 4.0558
        dtl = int(datetime.strptime("2021-05-31T17:27:48Z", "%Y-%m-%dT%H:%M:%SZ").timestamp())
        rl = 3.38
        self.assertEqual(int(calculate_bat_prediction(None, dti, ri, dtl, rl)), 0)

        # rl > ri -- return None
        dti = int(datetime.strptime("2021-05-10T03:03:46Z", "%Y-%m-%dT%H:%M:%SZ").timestamp())
        ri = 3.9
        dtl = int(datetime.strptime("2021-05-31T17:27:48Z", "%Y-%m-%dT%H:%M:%SZ").timestamp())
        rl = 3.99
        self.assertIsNone(calculate_bat_prediction(None, dti, ri, dtl, rl))

        # rl == ri -- return None
        dti = int(datetime.strptime("2021-05-10T03:03:46Z", "%Y-%m-%dT%H:%M:%SZ").timestamp())
        ri = 3.9
        dtl = int(datetime.strptime("2021-05-31T17:27:48Z", "%Y-%m-%dT%H:%M:%SZ").timestamp())
        rl = 3.9
        self.assertIsNone(calculate_bat_prediction(None, dti, ri, dtl, rl))

        # dti == dtl -- return None
        dti = int(datetime.strptime("2021-05-10T03:03:46Z", "%Y-%m-%dT%H:%M:%SZ").timestamp())
        ri = 3.9
        dtl = int(datetime.strptime("2021-05-10T03:03:46Z", "%Y-%m-%dT%H:%M:%SZ").timestamp())
        rl = 3.8
        self.assertIsNone(calculate_bat_prediction(None, dti, ri, dtl, rl))
