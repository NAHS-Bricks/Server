import boto3
from botocore.exceptions import ConnectionClosedError
from helpers.shared import config

botoClient = boto3.client('s3', endpoint_url=f"http://{config['s3']['server']}:{config['s3']['port']}", aws_access_key_id=config['s3']['access_key'], aws_secret_access_key=config['s3']['access_secret'])


def setup_storage():
    global botoClient
    if config['s3']['bucket'] not in [bucket['Name'] for bucket in botoClient.list_buckets()['Buckets']]:
        botoClient.create_bucket(Bucket=config['s3']['bucket'])


setup_storage()


def is_connected():
    global botoClient
    origCT = botoClient.meta.config.connect_timeout
    botoClient.meta.config.connect_timeout = 1
    origRetries = botoClient.meta.config.retries
    botoClient.meta.config.retries = {'max_attempts': 0}
    result = False
    for i in range(5):
        try:
            botoClient.list_buckets()
            result = True
            break
        except ConnectionClosedError:  # pragma: no cover
            continue
        except Exception:  # pragma: no cover
            break
    botoClient.meta.config.connect_timeout = origCT
    botoClient.meta.config.retries = origRetries
    return result


def firmware_get(brick_type=None, version=None, fwmetadata=None):
    """
    returns a firmware.bin from S3 storage

    brick_type = type of brick a firmware is meant to be for
    version = date-coded version string of firmware
    fwmetadata = Firmwaremetadata object, can be used to give brick_type and version
    """
    global botoClient
    if (brick_type is None or version is None) and fwmetadata is None:
        return None
    if fwmetadata is not None:
        brick_type = fwmetadata['brick_type']
        version = fwmetadata['version']
    result = botoClient.get_object(Bucket=config['s3']['bucket'], Key=f"firmware/{brick_type}_{version}.bin")
    return result['Body']


def firmware_save(content, brick_type=None, version=None, fwmetadata=None):
    """
    saves a firmware.bin to S3 storage

    content = fileobject opened as 'rb'
    brick_type = type of brick a firmware is meant to be for
    version = date-coded version string of firmware
    fwmetadata = Firmwaremetadata object, can be used to give brick_type and version
    """
    global botoClient
    if (brick_type is None or version is None) and fwmetadata is None:
        return False
    if fwmetadata is not None:
        brick_type = fwmetadata['brick_type']
        version = fwmetadata['version']
    try:
        botoClient.upload_fileobj(content, Bucket=config['s3']['bucket'], Key=f"firmware/{brick_type}_{version}.bin")
        return True
    except Exception:  # pragma: no cover
        return False


def firmware_delete(brick_type=None, version=None, fwmetadata=None):
    """
    deletes a firmware.bin from S3 storage

    brick_type = type of brick a firmware is meant to be for
    version = date-coded version string of firmware
    fwmetadata = Firmwaremetadata object, can be used to give brick_type and version
    """
    global botoClient
    if (brick_type is None or version is None) and fwmetadata is None:
        return False
    if fwmetadata is not None:
        brick_type = fwmetadata['brick_type']
        version = fwmetadata['version']
    try:
        botoClient.delete_object(Bucket=config['s3']['bucket'], Key=f"firmware/{brick_type}_{version}.bin")
        return True
    except Exception:  # pragma: no cover
        return False


def firmware_exists(brick_type=None, version=None, fwmetadata=None):
    """
    checks if a firmware.bin exists in S3 storage

    brick_type = type of brick a firmware is meant to be for
    version = date-coded version string of firmware
    fwmetadata = Firmwaremetadata object, can be used to give brick_type and version
    """
    global botoClient
    if (brick_type is None or version is None) and fwmetadata is None:
        return False
    if fwmetadata is not None:
        brick_type = fwmetadata['brick_type']
        version = fwmetadata['version']
    try:
        objects = botoClient.list_objects(Bucket=config['s3']['bucket'], Prefix=f"firmware/{brick_type}_{version}.bin")
        objects = [k for k in [obj['Key'] for obj in objects.get('Contents', [])]]
        if f"firmware/{brick_type}_{version}.bin" in objects:
            return True
        else:
            return False
    except Exception:  # pragma: no cover
        return False


def firmware_filename(brick_type=None, version=None, fwmetadata=None):
    """
    generates the filename for firmware from given attrs

    brick_type = type of brick a firmware is meant to be for
    version = date-coded version string of firmware
    fwmetadata = Firmwaremetadata object, can be used to give brick_type and version
    """
    if (brick_type is None or version is None) and fwmetadata is None:
        return None
    if fwmetadata is not None:
        brick_type = fwmetadata['brick_type']
        version = fwmetadata['version']
    return f"{brick_type}_{version}.bin"
