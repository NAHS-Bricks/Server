import boto3
from botocore.exceptions import ConnectionClosedError
from helpers.shared import config
from connector.mongodb import brick_all, brick_get, fwmetadata_exists, fwmetadata_save
from connector.s3 import firmware_exists, firmware_save
from datetime import datetime, timedelta
import json

if config['allow']['ds']:
    botoClient = boto3.client('s3', endpoint_url=f"https://{config['ds']['server']}:{config['ds']['port']}", aws_access_key_id=config['ds']['access_key'], aws_secret_access_key=config['ds']['access_secret'])
else:  # pragma: no cover
    botoClient = None

fw_sketch_map = {'cache': None, 'dt': None}


def is_connected():
    global botoClient
    if config['allow']['ds']:
        origCT = botoClient.meta.config.connect_timeout
        botoClient.meta.config.connect_timeout = 1
        origRetries = botoClient.meta.config.retries
        botoClient.meta.config.retries = {'max_attempts': 0}
        result = False
        for i in range(5):
            try:
                buckets = botoClient.list_buckets()
                result = True
                break
            except ConnectionClosedError:  # pragma: no cover
                continue
            except Exception:  # pragma: no cover
                break
        botoClient.meta.config.connect_timeout = origCT
        botoClient.meta.config.retries = origRetries

        if result:
            result = config['ds']['bucket'] in [bucket['Name'] for bucket in buckets['Buckets']]
        return result
    else:  # pragma: no cover
        return False


def _sketch_map():
    global botoClient
    global fw_sketch_map
    if config['allow']['ds']:
        if fw_sketch_map['dt'] is None or fw_sketch_map['dt'] < (datetime.now() - timedelta(minutes=10)).timestamp():
            sketch_map = botoClient.get_object(Bucket=config['ds']['bucket'], Key=f"fw-sketchMD5-map.json")
            fw_sketch_map['cache'] = json.loads(sketch_map['Body'].read().decode('utf-8'))
            fw_sketch_map['dt'] = datetime.now().timestamp()
        return fw_sketch_map['cache']
    return dict()  # pragma: no cover


def _sketch_map_get(brick_type, sketchMD5):
    if config['allow']['ds']:
        if str(brick_type) in _sketch_map() and sketchMD5 in _sketch_map()[str(brick_type)]:
            return _sketch_map()[str(brick_type)][sketchMD5]
    return None  # pragma: no cover


def dsfirmware_get(brick_type, version=None):
    """
    Fetches specific fwmetadata from downstream or latest for brick_type if version is None

    Returns firmware name if fwmetadata has been fetched or None is fwmetadata allready existed
    """
    global botoClient
    if config['allow']['ds']:
        if str(brick_type) not in _sketch_map():
            return None  # pragma: no cover
        if version is None:
            version = sorted(_sketch_map()[str(brick_type)].values(), reverse=True)[0]
        if not fwmetadata_exists(brick_type=brick_type, version=version):
            metadata = botoClient.get_object(Bucket=config['ds']['bucket'], Key=f"fw-metadata/{brick_type}_{version}.json")
            metadata = json.loads(metadata['Body'].read().decode('utf-8'))
            fwmetadata_save(metadata=metadata)
            return f"{brick_type}_{version}"
    return None


def dsfirmware_get_used(brick_id=None, brick=None):
    """
    Fetches fwmetadata from downstream of versions used on all bricks (if neither brick_id nor brick is given)
    or for a specific brick if brick_id or brick is given

    returns a list of all fetched fwmetadata names, can also be an empty list if all used fwmetadata is allready present
    """
    result = list()
    if config['allow']['ds']:
        if brick_id is not None:
            brick = brick_get(brick_id)
        if brick is not None:
            if brick.get('type') is not None and brick.get('sketchMD5') is not None:
                fw_version = _sketch_map_get(brick_type=brick.get('type'), sketchMD5=brick.get('sketchMD5'))
                fw_name = dsfirmware_get(brick_type=brick.get('type'), version=fw_version)
                if fw_name is not None:
                    result.append(fw_name)
        else:
            for brick_type, sketchMD5 in {(brick.get('type'), brick.get('sketchMD5')) for brick in brick_all()}:
                if brick_type is not None and sketchMD5 is not None:
                    fw_version = _sketch_map_get(brick_type=brick_type, sketchMD5=sketchMD5)
                    fw_name = dsfirmware_get(brick_type=brick_type, version=fw_version)
                    if fw_name is not None:
                        result.append(fw_name)
    return result


def dsfirmware_get_latest(brick_type=None):
    """
    Fetches latests fwmetadata from downstream for all used brick_types (if brick_type is None) or for a specific brick_type

    returns a list of all fetched fwmetadata names, can also be an empty list if all used fwmetadata is allready present
    """
    result = list()
    if config['allow']['ds']:
        if brick_type is not None:
            fw_name = dsfirmware_get(brick_type=brick_type)
            if fw_name is not None:
                result.append(fw_name)
        else:
            for bt in {brick.get('type') for brick in brick_all()}:
                if bt is not None:
                    fw_name = dsfirmware_get(brick_type=bt)
                    if fw_name is not None:
                        result.append(fw_name)
    return result


def dsfirmware_get_bin(brick_type, version=None):
    """
    Fetches specific firmware (bin) from downstream or latest for brick_type if version is None

    Returns firmware name if firmware (bin) has been fetched or None is firmware (bin) allready existed
    """
    global botoClient
    if config['allow']['ds']:
        if version is None:
            version = sorted(_sketch_map()[str(brick_type)].values(), reverse=True)[0]
        if not fwmetadata_exists(brick_type=brick_type, version=version):
            dsfirmware_get(brick_type=brick_type, version=version)
        if not firmware_exists(brick_type=brick_type, version=version):
            fw_bin = botoClient.get_object(Bucket=config['ds']['bucket'], Key=f"fw-bin/{brick_type}_{version}.bin")
            firmware_save(content=fw_bin['Body'], brick_type=brick_type, version=version)
            return f"{brick_type}_{version}"
    return None
