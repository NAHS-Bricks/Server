from pymongo import MongoClient
from helpers.shared import config, temp_sensor_defaults, latch_defaults
from helpers.feature_versioning import feature_update
import copy

mongoClient = MongoClient(host=config['mongo']['server'], port=int(config['mongo']['port']))
mongoDB = mongoClient.get_database(config['mongo']['database'])


def brick_get(brick_id):
    """
    Returns a brick from DB or a newly created it if doesn't exist in DB
    """
    global mongoDB
    brick = mongoDB.bricks.find_one({'_id': brick_id})
    if brick is None:
        brick = {}
        feature_update(brick, 'all', 0, 0)
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


def brick_all():
    """
    Returns an interator to all bricks in DB
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
    latch = mongoDB.latches.delete_one({'_id': lid})


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
