import requests
import json
from multiprocessing import Process, Queue
from connector.mongodb import start_mongodb_connection, mongodb_lock_acquire, mongodb_lock_release, brick_get
from stage.feature import feature_exec as exec_feature_stage
from stage.feedback import feedback_exec as exec_feedback_stage

async_queue = Queue()
async_process = None


def start_async_worker(test_suite=False):  # pragma: no cover
    def _async_worker(msg_queue, test_suite):
        start_mongodb_connection()
        while True:
            brick_id = msg_queue.get()
            if test_suite and brick_id == 'test_done':  # required for signaling a completed test
                open('/tmp/brick_activator', 'a').write(f"{brick_id}\n")
                continue
            if brick_id is None:
                continue
            mongodb_lock_acquire(brick_id)  # this is just to ensure, that a component that issued a brick activation is finished before the activation is executed
            brick = brick_get(brick_id)
            mongodb_lock_release(brick_id)
            if 'sleep' not in brick['features'] or (brick['features']['sleep'] >= 1.01 and brick['sleep_disabled']):
                if brick['ip'] is None:
                    continue  # if IP is unknown activation of brick is impossible
                if not test_suite:
                    try:
                        print(f"Activate: {brick['_id']}")
                        feature_requests = exec_feature_stage(brick)
                        feedback = json.dumps(exec_feedback_stage(brick, feature_requests=feature_requests, by_activator=True))
                        requests.post(f"http://{brick['ip']}/", headers={'Content-Type': 'application/json'}, data=feedback, timeout=2)
                        print(f"Activate: {brick['_id']} Feedback: {feedback}")
                    except Exception as e:
                        print(f"Activate: {brick['_id']} Error: {e}")
                else:
                    feature_requests = exec_feature_stage(brick)
                    feedback = json.dumps(exec_feedback_stage(brick, feature_requests=feature_requests, by_activator=True))
                    open('/tmp/brick_activator', 'a').write(f"{brick['_id']}={feedback}\n")

    global async_queue
    global async_process
    if async_process is None:
        async_process = Process(target=_async_worker, args=(async_queue, test_suite, ), daemon=True)
        async_process.start()


def activate(brick=None, brick_id=None):
    global async_queue
    if brick is not None:
        async_queue.put(brick['_id'])
    else:
        async_queue.put(brick_id)
