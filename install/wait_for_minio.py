import sys
import os
import time
import boto3
from botocore.client import Config
from botocore.exceptions import EndpointConnectionError, ConnectionClosedError
sys.path.append(os.getcwd())
from helpers.shared import config

botoConfig = Config(connect_timeout=1, retries={'max_attempts': 0})
botoClient = boto3.client('s3', endpoint_url=f"http://{config['s3']['server']}:{config['s3']['port']}", aws_access_key_id=config['s3']['access_key'], aws_secret_access_key=config['s3']['access_secret'], config=botoConfig)
while(True):
    try:
        botoClient.list_buckets()
        print("MinIO started ... continue", flush=True)
        sys.exit(0)
    except EndpointConnectionError:
        print("MinIO pending ... waiting", flush=True)
        time.sleep(1)
    except ConnectionClosedError:
        print("MinIO pending ... waiting", flush=True)
        time.sleep(1)
    except Exception:
        print("MinIO unknown error ... aborting", flush=True)
        sys.exit(1)
