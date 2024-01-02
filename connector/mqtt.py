import paho.mqtt.client as mqtt
from helpers.shared import config
from multiprocessing import Process, Queue

async_queue = Queue()
async_process = None


def _mqttClient():
    mqttClient = mqtt.Client(client_id=config['mqtt']['clientid'], protocol=mqtt.MQTTv5, transport='tcp')
    mqttClient.connect(config['mqtt']['server'], port=config['mqtt']['port'])
    return mqttClient


def start_async_worker():  # pragma: no cover
    def _async_worker(msg_queue):
        while True:
            topic, payload = msg_queue.get()
            if topic is not None and payload is not None:
                mqttClient = _mqttClient()
                mqttClient.loop_start()
                mqttClient.publish(topic, payload, qos=2)
                mqttClient.loop_stop()
                mqttClient.disconnect()

    global async_queue
    global async_process
    if async_process is None:
        async_process = Process(target=_async_worker, args=(async_queue, ), daemon=True)
        async_process.start()


def is_connected():
    try:
        mqttClient = _mqttClient()
        mqttClient.disconnect()
        return True
    except Exception:  # pragma: no cover
        return False


def _publish_async(topic=None, payload=None):
    global async_queue
    async_queue.put((topic, payload))


def temp_send(sensor_id, celsius, brick_id):
    _publish_async(f"brick/{brick_id}/temp/{sensor_id}", float(celsius))


def humid_send(sensor_id, humidity, brick_id):
    _publish_async(f"brick/{brick_id}/humid/{sensor_id}", float(humidity))


def latch_send(latch_id, state):
    brick_id, _ = latch_id.split('_')
    _publish_async(f"brick/{brick_id}/latch/{latch_id}", int(state))


def signal_send(signal_id, state, transmitted=False):
    brick_id, _ = signal_id.split('_')
    if not transmitted:
        state += 10
    _publish_async(f"brick/{brick_id}/signal/{signal_id}", int(state))


def heater_send(heater_id, state, transmitted=False):
    # heater_id equals brick_id in this case
    if not transmitted:
        state += 10
    _publish_async(f"brick/{heater_id}/heater", int(state))


def bat_level_send(brick_id, voltage, prediction=None):
    _publish_async(f"brick/{brick_id}/bat/voltage", float(voltage))
    if prediction is not None:
        _publish_async(f"brick/{brick_id}/bat/prediction", float(prediction))


def bat_charging_send(brick_id, charging=False, standby=False):
    state = 0
    if charging:
        state = 1
    elif standby:
        state = 2
    _publish_async(f"brick/{brick_id}/bat/charging", state)


def fanctl_state_send(fanctl_id, state, rps=None, received=False):
    brick_id, _ = fanctl_id.split('_')
    if not received:
        state += 10
    _publish_async(f"brick/{brick_id}/fanctl/{fanctl_id}/state", int(state))
    if received and rps is not None:
        _publish_async(f"brick/{brick_id}/fanctl/{fanctl_id}/rps", int(rps))


def fanctl_duty_send(fanctl_id, duty):
    brick_id, _ = fanctl_id.split('_')
    _publish_async(f"brick/{brick_id}/fanctl/{fanctl_id}/duty", int(duty))
