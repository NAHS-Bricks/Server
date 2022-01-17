from ._wrapper import *
from connector.mongodb import fwmetadata_save
import zipfile
import tempfile
import warnings


@parameterized_class(getVersionParameter('os', minVersion={'os': 1.01}))
class OtaInterface(BaseCherryPyTestCase):
    def setUp(self):
        warnings.simplefilter("ignore", ResourceWarning)

    def tearDown(self):
        warnings.simplefilter("default", ResourceWarning)

    def test_from_none_sketchMD5(self):
        response = self.webapp_request(clear_state=True, v=self.v, x=1)
        with tempfile.SpooledTemporaryFile() as tf:
            with zipfile.ZipFile(tf, 'w') as zf:
                zf.writestr('metadata.json', json.dumps({'version': '202112201800', 'brick_type': 1, 'content': {}, 'sketchMD5': '1234'}))
                zf.writestr('firmware.bin', b'Hallo Welt')
            tf.seek(0)
            response = self.webapp_request(path='/upload', files={'firmware': tf})
        response = self.webapp_request(path='/ota', method='get')
        self.assertTrue(response.status.startswith('200'))
        self.assertEqual(response.state['otaUpdate'], 'running')

    def test_from_old_sketchMD5(self):
        response = self.webapp_request(clear_state=True, v=self.v, x=1, m='0123')
        with tempfile.SpooledTemporaryFile() as tf:
            with zipfile.ZipFile(tf, 'w') as zf:
                zf.writestr('metadata.json', json.dumps({'version': '202112201800', 'brick_type': 1, 'content': {}, 'sketchMD5': '1234'}))
                zf.writestr('firmware.bin', b'Hallo Welt')
            tf.seek(0)
            response = self.webapp_request(path='/upload', files={'firmware': tf})
        response = self.webapp_request(path='/ota', method='get')
        self.assertTrue(response.status.startswith('200'))
        self.assertEqual(response.state['otaUpdate'], 'running')

    def test_brick_allready_uptodate(self):
        response = self.webapp_request(clear_state=True, v=self.v, x=1, m='1234')  # set sketchMD5 to the newest
        with tempfile.SpooledTemporaryFile() as tf:
            with zipfile.ZipFile(tf, 'w') as zf:
                zf.writestr('metadata.json', json.dumps({'version': '202112201800', 'brick_type': 1, 'content': {}, 'sketchMD5': '1234'}))
                zf.writestr('firmware.bin', b'Hallo Welt')
            tf.seek(0)
            response = self.webapp_request(path='/upload', files={'firmware': tf})
        response = self.webapp_request(path='/ota', method='get')
        self.assertTrue(response.status.startswith('304'))
        self.assertEqual(response.state['otaUpdate'], 'skipped')

    def test_no_fwmetadata_available(self):
        response = self.webapp_request(clear_state=True, v=self.v, x=1)
        response = self.webapp_request(path='/ota', method='get')
        self.assertTrue(response.status.startswith('304'))
        self.assertEqual(response.state['otaUpdate'], 'skipped')

    def test_no_firmware_available(self):
        response = self.webapp_request(clear_state=True, v=self.v, x=1)
        fwmetadata_save({'version': '202112201800', 'brick_type': 1, 'content': {}, 'sketchMD5': '1234'})
        response = self.webapp_request(path='/ota', method='get')
        self.assertTrue(response.status.startswith('304'))
        self.assertEqual(response.state['otaUpdate'], 'skipped')


@parameterized_class(getVersionParameter('os', specificVersion=[['os', 1.00]]))
class OtaInterfaceWithOs100(BaseCherryPyTestCase):
    def setUp(self):
        warnings.simplefilter("ignore", ResourceWarning)

    def tearDown(self):
        warnings.simplefilter("default", ResourceWarning)

    def test_ota_update_wrong_os_version(self):
        response = self.webapp_request(clear_state=True, v=self.v, x=1)
        with tempfile.SpooledTemporaryFile() as tf:
            with zipfile.ZipFile(tf, 'w') as zf:
                zf.writestr('metadata.json', json.dumps({'version': '202112201800', 'brick_type': 1, 'content': {}, 'sketchMD5': '1234'}))
                zf.writestr('firmware.bin', b'Hallo Welt')
            tf.seek(0)
            response = self.webapp_request(path='/upload', files={'firmware': tf})
        response = self.webapp_request(path='/ota', method='get')
        self.assertTrue(response.status.startswith('304'))
        self.assertNotIn('otaUpdate', response.state)
