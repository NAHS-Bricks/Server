import pika
from helpers.shared import config, event_worker_is_running
import json
import time

rabbitConn = None
rabbitMQ = None


def _connect():
    global rabbitConn
    global rabbitMQ
    if rabbitConn is None or not rabbitConn.is_open:
        rabbitConn = pika.BlockingConnection(pika.ConnectionParameters(host=config['rabbit']['server'], port=config['rabbit']['port']))
    if rabbitMQ is None or not rabbitMQ.is_open:
        rabbitMQ = rabbitConn.channel()
        rabbitMQ.queue_declare(queue='events')


def event_create(brick, brick_old=None, retry=True):
    _connect()
    global rabbitMQ
    try:
        rabbitMQ.basic_publish(
            exchange='',
            routing_key='events',
            body=json.dumps((brick, brick_old))
        )
    except pika.exceptions.StreamLostError:  # pragma: no cover
        if retry:
            event_create(brick, brick_old, False)


def wait_for_all_events_done():
    _connect()
    global rabbitMQ
    done = False
    while not done:
        time.sleep(0.01)
        try:
            event_worker_is_running.acquire()
            done = False
            if rabbitMQ.queue_declare(queue='events', passive=True).method.message_count == 0:
                event_worker_is_running.release()
                time.sleep(0.01)
                event_worker_is_running.acquire()
                done = True
        except Exception:  # pragma: no cover
            pass
        finally:
            event_worker_is_running.release()
