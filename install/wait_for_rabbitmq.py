import pika
from pika import exceptions
import sys
import time

while(True):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', port=5672))
        print("RabbitMQ started ... continue", flush=True)
        sys.exit(0)
    except exceptions.AMQPConnectionError:
        print("RabbitMQ pending ... waiting", flush=True)
        time.sleep(1)
    except Exception:
        print("RabbitMQ unknown error ... aborting", flush=True)
        sys.exit(1)
