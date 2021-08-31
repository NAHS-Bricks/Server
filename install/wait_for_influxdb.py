import sys
import os
import time
from influxdb import InfluxDBClient
from requests import exceptions
sys.path.append(os.getcwd())
from helpers.shared import config

influxDB = InfluxDBClient(host=config['influx']['server'], port=config['influx']['port'])

while(True):
    try:
        influxDB.get_list_database()
        print("InfluxDB started ... continue", flush=True)
        sys.exit(0)
    except exceptions.ConnectionError:
        print("InfluxDB pending ... waiting", flush=True)
        time.sleep(1)
    except Exception:
        print("InfluxDB unknown error ... aborting", flush=True)
        sys.exit(1)
