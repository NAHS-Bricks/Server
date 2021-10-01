from pymongo import MongoClient, ASCENDING
from helpers.shared import config, temp_sensor_defaults, latch_defaults, signal_defaults, humid_defaults
from helpers.feature_versioning import feature_update
import copy
from bson.objectid import ObjectId
from threading import Lock

mongoClient = None
mongoDB = None
brick_locks = {}
brick_locks_modifier_lock = Lock()


def start_mongodb_connection():
    global mongoClient
    global mongoDB
    if mongoClient is None:
        mongoClient = MongoClient(host=config['mongo']['server'], port=int(config['mongo']['port']))
        mongoDB = mongoClient.get_database(config['mongo']['database'])


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


"""
brick
"""


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


"""
temp
"""


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


"""
humid
"""


def humid_get(sensor_id):
    """
    Returns a humidity sensor from DB or a newly created it if doesn't exist in DB
    """
    global mongoDB
    sensor = mongoDB.humid_sensors.find_one({'_id': sensor_id})
    if sensor is None:
        sensor = {}
        sensor.update(copy.deepcopy(humid_defaults))
        sensor['_id'] = sensor_id
    return sensor


def humid_save(sensor):
    """
    Saves humidity sensor to DB
    """
    global mongoDB
    mongoDB.humid_sensors.replace_one({'_id': sensor['_id']}, sensor, True)


def humid_delete(sensor_id):
    """
    Removes humidity sensor from DB
    """
    global mongoDB
    mongoDB.humid_sensors.delete_one({'_id': sensor_id})


def humid_exists(sensor_id):
    """
    Returns True or False whether a humidity sensor is stored in DB or not
    """
    global mongoDB
    sensor = mongoDB.humid_sensors.find_one({'_id': sensor_id})
    if sensor is not None:
        return True
    return False


def humid_all():  # pragma: no cover
    """
    Returns an iterator to all humidity sensors in DB
    """
    global mongoDB
    return mongoDB.humid_sensors.find({})


def humid_count():
    """
    Returns number of humidity sensors present in DB
    """
    global mongoDB
    return mongoDB.humid_sensors.count_documents({})


"""
latch
"""


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


"""
signal
"""


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


"""
util
"""


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
