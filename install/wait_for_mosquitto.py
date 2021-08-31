import sys
import os
import time
import paho.mqtt.client as mqtt
sys.path.append(os.getcwd())
from helpers.shared import config

mqttClient = mqtt.Client(client_id=config['mqtt']['clientid'], protocol=mqtt.MQTTv5, transport='tcp')
while(True):
    try:
        mqttClient.connect(config['mqtt']['server'], port=config['mqtt']['port'])
        print("Mosqitto started ... continue", flush=True)
        sys.exit(0)
    except ConnectionRefusedError:
        print("Mosqitto pending ... waiting", flush=True)
        time.sleep(1)
    except Exception:
        print("Mosqitto unknown error ... aborting", flush=True)
        sys.exit(1)
