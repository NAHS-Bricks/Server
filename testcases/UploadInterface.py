from ._wrapper import *
from connector.s3 import firmware_exists
from connector.mongodb import fwmetadata_exists
import tempfile
import zipfile
import warnings


class UploadInterface(BaseCherryPyTestCase):
    def setUp(self):
        warnings.simplefilter("ignore", ResourceWarning)

    def tearDown(self):
        warnings.simplefilter("default", ResourceWarning)

    def test_firmware_sunshine_upload(self):
        response = self.webapp_request(clear_state=True)
        self.assertFalse(firmware_exists(1, '202112201800'))
        self.assertFalse(fwmetadata_exists(1, '202112201800'))
        with tempfile.SpooledTemporaryFile() as tf:
            with zipfile.ZipFile(tf, 'w') as zf:
                zf.writestr('metadata.json', json.dumps({'version': '202112201800', 'brick_type': 1, 'content': {}, 'sketchMD5': '1234'}))
                zf.writestr('firmware.bin', b'Hallo Welt')
            tf.seek(0)
            response = self.webapp_request(path='/upload', files={'firmware': tf})
        self.assertIn('s', response.json)
        self.assertEqual(response.json['s'], 0)
        self.assertTrue(firmware_exists(1, '202112201800'))
        self.assertTrue(fwmetadata_exists(1, '202112201800'))

    def test_firmware_file_to_big(self):
        c = ""
        for i in range(100000, 450000):
            c += str(i)
        with tempfile.SpooledTemporaryFile() as tf:
            tf.write(c.encode())
            tf.seek(0)
            response = self.webapp_request(path='/upload', files={'firmware': tf})
        self.assertIn('s', response.json)
        self.assertEqual(response.json['s'], 2)  # file size is to big

    def test_firmware_missing_files(self):
        response = self.webapp_request(path='/upload', files={})
        self.assertIn('s', response.json)
        self.assertEqual(response.json['s'], 1)  # missing firmware package

        with tempfile.SpooledTemporaryFile() as tf:
            with zipfile.ZipFile(tf, 'w') as zf:
                zf.writestr('metadata.json', json.dumps({'version': '202112201800', 'brick_type': 1, 'content': {}, 'sketchMD5': '1234'}))
            tf.seek(0)
            response = self.webapp_request(path='/upload', files={'firmware': tf})
        self.assertIn('s', response.json)
        self.assertEqual(response.json['s'], 4)  # firmware.bin is missing in firmware package

        with tempfile.SpooledTemporaryFile() as tf:
            with zipfile.ZipFile(tf, 'w') as zf:
                zf.writestr('firmware.bin', b'Hallo Welt')
            tf.seek(0)
            response = self.webapp_request(path='/upload', files={'firmware': tf})
        self.assertIn('s', response.json)
        self.assertEqual(response.json['s'], 3)  # metadata.json is missing in firmware package

    def test_firmware_missing_data_in_metadata(self):
        with tempfile.SpooledTemporaryFile() as tf:
            with zipfile.ZipFile(tf, 'w') as zf:
                zf.writestr('metadata.json', '{"brick_type": 1 "version": "202112201800", "content": {}, "sketchMD5": "1234"}')  # there is a , missing
                zf.writestr('firmware.bin', b'Hallo Welt')
            tf.seek(0)
            response = self.webapp_request(path='/upload', files={'firmware': tf})
        self.assertIn('s', response.json)
        self.assertEqual(response.json['s'], 9)  # metadata.json is not a valid json file

        with tempfile.SpooledTemporaryFile() as tf:
            with zipfile.ZipFile(tf, 'w') as zf:
                zf.writestr('metadata.json', json.dumps({'brick_type': 1, 'content': {}, 'sketchMD5': '1234'}))
                zf.writestr('firmware.bin', b'Hallo Welt')
            tf.seek(0)
            response = self.webapp_request(path='/upload', files={'firmware': tf})
        self.assertIn('s', response.json)
        self.assertEqual(response.json['s'], 6)  # version missing in metadata

        with tempfile.SpooledTemporaryFile() as tf:
            with zipfile.ZipFile(tf, 'w') as zf:
                zf.writestr('metadata.json', json.dumps({'version': '202112201800', 'content': {}, 'sketchMD5': '1234'}))
                zf.writestr('firmware.bin', b'Hallo Welt')
            tf.seek(0)
            response = self.webapp_request(path='/upload', files={'firmware': tf})
        self.assertIn('s', response.json)
        self.assertEqual(response.json['s'], 5)  # brick_type missing in metadata

        with tempfile.SpooledTemporaryFile() as tf:
            with zipfile.ZipFile(tf, 'w') as zf:
                zf.writestr('metadata.json', json.dumps({'version': '202112201800', 'brick_type': 1, 'sketchMD5': '1234'}))
                zf.writestr('firmware.bin', b'Hallo Welt')
            tf.seek(0)
            response = self.webapp_request(path='/upload', files={'firmware': tf})
        self.assertIn('s', response.json)
        self.assertEqual(response.json['s'], 8)  # content missing in metadata

        with tempfile.SpooledTemporaryFile() as tf:
            with zipfile.ZipFile(tf, 'w') as zf:
                zf.writestr('metadata.json', json.dumps({'version': '202112201800', 'brick_type': 1, 'content': {}}))
                zf.writestr('firmware.bin', b'Hallo Welt')
            tf.seek(0)
            response = self.webapp_request(path='/upload', files={'firmware': tf})
        self.assertIn('s', response.json)
        self.assertEqual(response.json['s'], 7)  # sketchMD5 missing in metadata
