from influxdb import InfluxDBClient
from requests import exceptions
import sys
import time

influxDB = InfluxDBClient(host='localhost', port=8086)

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
