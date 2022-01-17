from ._wrapper import *
from connector.s3 import firmware_get, firmware_save, firmware_exists, firmware_delete, firmware_filename
import tempfile


class ConnecorS3(BaseCherryPyTestCase):
    def test_creating_firmware(self):
        response = self.webapp_request(clear_state=True)
        self.assertFalse(firmware_exists(1, '202112211800'))
        self.assertFalse(firmware_exists(1, '202112211900'))
        with tempfile.SpooledTemporaryFile() as tf:
            tf.write(b'Hallo Welt1')
            tf.seek(0)
            firmware_save(tf, 1, '202112211800')
        self.assertTrue(firmware_exists(1, '202112211800'))
        self.assertFalse(firmware_exists(1, '202112211900'))
        with tempfile.SpooledTemporaryFile() as tf:
            tf.write(b'Hallo Welt2')
            tf.seek(0)
            fwm = {'brick_type': 1, 'version': '202112211900'}
            firmware_save(tf, fwmetadata=fwm)  # creating it with fwmetadata
        self.assertTrue(firmware_exists(1, '202112211800'))
        self.assertTrue(firmware_exists(1, '202112211900'))

    def test_getting_firmware(self):
        response = self.webapp_request(clear_state=True)
        with tempfile.SpooledTemporaryFile() as tf:
            tf.write(b'Hallo Welt1')
            tf.seek(0)
            firmware_save(tf, 1, '202112211800')
        with tempfile.SpooledTemporaryFile() as tf:
            tf.write(b'Hallo Welt2')
            tf.seek(0)
            firmware_save(tf, 1, '202112211900')
        self.assertTrue(firmware_exists(1, '202112211800'))
        self.assertTrue(firmware_exists(1, '202112211900'))

        self.assertEqual(firmware_get(1, '202112211800').read(), b'Hallo Welt1')
        self.assertEqual(firmware_get(1, '202112211900').read(), b'Hallo Welt2')
        fwm = {'brick_type': 1, 'version': '202112211800'}
        self.assertEqual(firmware_get(fwmetadata=fwm).read(), b'Hallo Welt1')  # getting it with fwmetadata

    def test_deleting_firmware(self):
        response = self.webapp_request(clear_state=True)
        with tempfile.SpooledTemporaryFile() as tf:
            tf.write(b'Hallo Welt1')
            tf.seek(0)
            firmware_save(tf, 1, '202112211800')
        with tempfile.SpooledTemporaryFile() as tf:
            tf.write(b'Hallo Welt2')
            tf.seek(0)
            firmware_save(tf, 1, '202112211900')
        self.assertTrue(firmware_exists(1, '202112211800'))
        self.assertTrue(firmware_exists(1, '202112211900'))

        self.assertTrue(firmware_delete(1, '202112211800'))
        self.assertFalse(firmware_exists(1, '202112211800'))

        fwm = {'brick_type': 1, 'version': '202112211900'}
        self.assertTrue(firmware_exists(fwmetadata=fwm))  # testing existence with fwmetadata

        self.assertTrue(firmware_delete(fwmetadata=fwm))  # deleting it with fwmetadata
        self.assertFalse(firmware_exists(1, '202112211800'))
        self.assertFalse(firmware_exists(1, '202112211900'))

    def test_generating_firmware_filename(self):
        response = self.webapp_request(clear_state=True)
        self.assertEqual(firmware_filename(1, '202112211800'), '1_202112211800.bin')

        fwm = {'brick_type': 1, 'version': '202112211900'}
        self.assertEqual(firmware_filename(fwmetadata=fwm), '1_202112211900.bin')  # testing generation with fwmetadata

    def test_invalid_attr(self):
        with tempfile.SpooledTemporaryFile() as tf:
            tf.write(b'Hallo Welt1')
            tf.seek(0)
            self.assertFalse(firmware_save(tf))
        self.assertFalse(firmware_exists())
        self.assertFalse(firmware_delete())
        self.assertIsNone(firmware_get())
        self.assertIsNone(firmware_filename())
