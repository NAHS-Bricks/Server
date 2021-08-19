from pymongo import MongoClient, ASCENDING
from helpers.shared import config, temp_sensor_defaults, latch_defaults, signal_defaults, event_defaults
from helpers.feature_versioning import feature_update
import copy
from bson.objectid import ObjectId
from threading import Lock

mongoClient = MongoClient(host=config['mongo']['server'], port=int(config['mongo']['port']))
mongoDB = mongoClient.get_database(config['mongo']['database'])
brick_locks = {}
brick_locks_modifier_lock = Lock()


def mongodb_lock_acquire(brick_id):
    global brick_locks
    global brick_locks_modifier_lock
    brick_locks_modifier_lock.acquire()
    if brick_id not in brick_locks:
        brick_locks[brick_id] = Lock()
    brick_locks_modifier_lock.release()
    brick_locks[brick_id].acquire()


def mongodb_lock_release(brick_id):
    global brick_locks
    brick_locks[brick_id].release()


def brick_get(brick_id):
    """
    Returns a brick from DB or a newly created it if doesn't exist in DB
    """
    global mongoDB
    brick = mongoDB.bricks.find_one({'_id': brick_id})
    if brick is None:
        brick = {}
        feature_update(brick, 'all', -1, 0)
        brick['_id'] = brick_id
    return brick


def brick_save(brick):
    """
    Saves brick to DB
    """
    global mongoDB
    mongoDB.bricks.replace_one({'_id': brick['_id']}, brick, True)


def brick_delete(brick_id):
    """
    Removes brick from DB
    """
    global mongoDB
    mongoDB.bricks.delete_one({'_id': brick_id})


def brick_exists(brick_id):
    """
    Returns True or False whether a brick is stored in DB or not
    """
    global mongoDB
    brick = mongoDB.bricks.find_one({'_id': brick_id})
    if brick is not None:
        return True
    return False


def brick_all():  # pragma: no cover
    """
    Returns an iterator to all bricks in DB
    """
    global mongoDB
    return mongoDB.bricks.find({})


def brick_all_ids():
    """
    Returns a list of all brick's id's present in DB
    """
    global mongoDB
    ids = []
    for brick in mongoDB.bricks.find({}):
        ids.append(brick['_id'])
    return ids


def brick_count():
    """
    Returns number of bricks present in DB
    """
    global mongoDB
    return mongoDB.bricks.count_documents({})


def temp_sensor_get(sensor_id):
    """
    Returns a temp_sensor from DB or a newly created it if doesn't exist in DB
    """
    global mongoDB
    sensor = mongoDB.temp_sensors.find_one({'_id': sensor_id})
    if sensor is None:
        sensor = {}
        sensor.update(copy.deepcopy(temp_sensor_defaults))
        sensor['_id'] = sensor_id
    return sensor


def temp_sensor_save(sensor):
    """
    Saves temp_sensor to DB
    """
    global mongoDB
    mongoDB.temp_sensors.replace_one({'_id': sensor['_id']}, sensor, True)


def temp_sensor_delete(sensor_id):
    """
    Removes temp_sensor from DB
    """
    global mongoDB
    mongoDB.temp_sensors.delete_one({'_id': sensor_id})


def temp_sensor_exists(sensor_id):
    """
    Returns True or False whether a temp_sensor is stored in DB or not
    """
    global mongoDB
    sensor = mongoDB.temp_sensors.find_one({'_id': sensor_id})
    if sensor is not None:
        return True
    return False


def temp_sensor_all():  # pragma: no cover
    """
    Returns an iterator to all temp_sensors in DB
    """
    global mongoDB
    return mongoDB.temp_sensors.find({})


def temp_sensor_count():
    """
    Returns number of tempsensors present in DB
    """
    global mongoDB
    return mongoDB.temp_sensors.count_documents({})


def latch_get(brick_id, latch_id):
    """
    Returns a latch from DB or a newly created it if doesn't exist in DB
    """
    global mongoDB
    lid = brick_id + '_' + str(latch_id)
    latch = mongoDB.latches.find_one({'_id': lid})
    if latch is None:
        latch = dict()
        latch.update(copy.deepcopy(latch_defaults))
        latch['_id'] = lid
    return latch


def latch_save(latch):
    """
    Saves latch to DB
    """
    global mongoDB
    mongoDB.latches.replace_one({'_id': latch['_id']}, latch, True)


def latch_delete(brick_id, latch_id):
    """
    Removes latch from DB
    """
    global mongoDB
    lid = brick_id + '_' + str(latch_id)
    mongoDB.latches.delete_one({'_id': lid})


def latch_exists(brick_id, latch_id):
    """
    Returns True or False whether a latch is stored in DB or not
    """
    global mongoDB
    lid = brick_id + '_' + str(latch_id)
    latch = mongoDB.latches.find_one({'_id': lid})
    if latch is not None:
        return True
    return False


def latch_all():  # pragma: no cover
    """
    Returns an iterator to all latches in DB
    """
    global mongoDB
    return mongoDB.latches.find({})


def latch_count():
    """
    Returns number of latches present in DB
    """
    global mongoDB
    return mongoDB.latches.count_documents({})


def signal_get(brick_id, signal_id):
    """
    Returns a signal from DB or a newly created it if doesn't exist in DB
    """
    global mongoDB
    sid = brick_id + '_' + str(signal_id)
    signal = mongoDB.signals.find_one({'_id': sid})
    if signal is None:
        signal = dict()
        signal.update(copy.deepcopy(signal_defaults))
        signal['_id'] = sid
    return signal


def signal_save(signal):
    """
    Saves signal to DB
    """
    global mongoDB
    mongoDB.signals.replace_one({'_id': signal['_id']}, signal, True)


def signal_delete(signal):
    """
    Removes signal from DB
    """
    global mongoDB
    mongoDB.signals.delete_one({'_id': signal['_id']})


def signal_exists(brick_id, signal_id):
    """
    Returns True or False whether a signal is stored in DB or not
    """
    global mongoDB
    sid = brick_id + '_' + str(signal_id)
    signal = mongoDB.signals.find_one({'_id': sid})
    if signal is not None:
        return True
    return False


def signal_all(brick_id=None):  # pragma: no cover
    """
    Returns an iterator to all signals in DB if brick_id is None
    Otherwise returns an iterator to all signals of a specific brick
    """
    global mongoDB
    if brick_id is None:
        return mongoDB.signals.find({}).sort("_id", ASCENDING)
    else:
        return mongoDB.signals.find({'_id': {'$regex': '^' + str(brick_id) + '_'}}).sort("_id", ASCENDING)


def signal_count():
    """
    Returns number of signals present in DB
    """
    global mongoDB
    return mongoDB.signals.count_documents({})


def event_get(event_id=None):
    """
    Returns an event from DB or a newly created it if doesn't exist in DB
    """
    global mongoDB
    if event_id is not None:
        event = mongoDB.events.find_one({'_id': event_id})
    if event_id is None or event is None:
        event = dict()
        event.update(copy.deepcopy(event_defaults))
        event['_id'] = str(ObjectId())
    return event


def event_save(event):
    """
    Saves event to DB
    """
    global mongoDB
    mongoDB.events.replace_one({'_id': event['_id']}, event, True)


def event_delete(event):
    """
    Removes event from DB
    """
    global mongoDB
    mongoDB.events.delete_one({'_id': event['_id']})


def event_exists(event_id):
    """
    Returns True or False whether a event is stored in DB or not
    """
    global mongoDB
    event = mongoDB.events.find_one({'_id': event_id})
    return event is not None


def event_all(brick_id=None):  # pragma: no cover
    """
    Returns an iterator to all events in DB if brick_id is None
    Otherwise returns an iterator to all events of a specific brick
    """
    global mongoDB
    if brick_id is None:
        return mongoDB.events.find({}).sort("_id", ASCENDING)
    else:
        return mongoDB.events.find({'brick_id': str(brick_id)}).sort("_id", ASCENDING)


def event_count():
    """
    Returns number of events present in DB
    """
    global mongoDB
    return mongoDB.events.count_documents({})


def event_data_get(event, name):
    """
    Returns event_data from DB or a newly created it if doesn't exist in DB
    """
    global mongoDB
    if name.startswith('__'):
        edid = str(name.replace('__', 'g_', 1))
    elif name.startswith('_'):
        edid = str(event['brick_id']) + str(name)
    else:
        edid = str(event['_id']) + '_' + str(name)
    event_data = mongoDB.event_data.find_one({'_id': edid})
    if event_data is None:
        event_data = dict()
        event_data['_id'] = edid
    return event_data


def event_data_save(event_data):
    """
    Saves event_data to DB
    """
    global mongoDB
    mongoDB.event_data.replace_one({'_id': event_data['_id']}, event_data, True)


def event_data_delete(event_data):
    """
    Removes event_data from DB
    """
    global mongoDB
    mongoDB.event_data.delete_one({'_id': event_data['_id']})


def event_data_all(scope=None):  # pragma: no cover
    """
    Returns an iterator to all event_data in DB if scope is None
    Otherwise returns an iterator to all event_data of a specific scope
      this can either be <event_id>, <brick_id> or g
    """
    global mongoDB
    if scope is None:
        return mongoDB.event_data.find({}).sort("_id", ASCENDING)
    else:
        return mongoDB.event_data.find({'_id': {'$regex': '^' + str(scope) + '_'}}).sort("_id", ASCENDING)


def event_data_count():
    """
    Returns number of event_data present in DB
    """
    global mongoDB
    return mongoDB.event_data.count_documents({})


def util_get(util_id):
    """
    Returns a util from DB or a newly created it if doesn't exist in DB
    """
    global mongoDB
    util = mongoDB.util.find_one({'_id': util_id})
    if util is None:
        util = {'_id': util_id}
    return util


def util_save(util):
    """
    Saves util to DB
    """
    global mongoDB
    mongoDB.util.replace_one({'_id': util['_id']}, util, True)
