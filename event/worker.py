import pika
import json
import cherrypy
import builtins
from helpers.shared import config
from helpers.mongodb import event_get, event_data_get
from event.commands import commands as event_command
from event.reactions import reactions as event_reaction
from helpers.shared import event_worker_is_running
from threading import Thread


def _callback(ch, method, properties, body):
    try:
        event_worker_is_running.acquire()
        # disable all prints during testing
        if 'environment' in cherrypy.config and cherrypy.config['environment'] == 'test_suite':  # pragma: no cover
            def print(*args, **kwargs):
                pass
        else:
            def print(*args, **kwargs):  # pragma: no cover
                return builtins.print(*args, **kwargs)

        brick, brick_old = json.loads(body.decode())
        print(f"\nEvent-System: executes {len(brick['events'])} events for brick {brick['_id']}")
        for event in [event_get(eid) for eid in brick['events']]:
            if isinstance(event['command'], list) and len(event['command']) == 2:
                command, ed_name = event['command']
                ed = event_data_get(event, ed_name)
                print(f"|--Command: '{command}' with {ed}")
                if command in event_command and event_command[command](event, ed, brick, brick_old):
                    for reaction, ed_name in event['reactions']:
                        ed = event_data_get(event, ed_name)
                        print(f"|  |--Reaction: '{reaction}' with {ed}")
                        if reaction in event_reaction:
                            event_reaction[reaction](event, ed)
    except Exception as e:  # pragma: no cover
        print(f"---Error: {e}")
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)
        event_worker_is_running.release()


def start():
    rabbitConn = pika.BlockingConnection(pika.ConnectionParameters(host=config['rabbit']['server'], port=config['rabbit']['port']))
    rabbitMQ = rabbitConn.channel()
    rabbitMQ.queue_declare(queue='events')
    rabbitMQ.basic_qos(prefetch_count=1)
    rabbitMQ.basic_consume(queue='events', on_message_callback=_callback)
    rabbitMQ.start_consuming()


def start_thread():
    worker_thread = Thread(target=start, daemon=True)
    worker_thread.start()
