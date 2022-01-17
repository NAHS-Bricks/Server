from influxdb import InfluxDBClient
from helpers.shared import config
import json
from datetime import datetime
from multiprocessing import Process, Queue

influxDB = InfluxDBClient(host=config['influx']['server'], port=int(config['influx']['port']))
async_queue = Queue()
async_process = None


def setup_database():
    global influxDB
    db_name = config['influx']['database']

    # create database
    if db_name not in [db['name'] for db in influxDB.get_list_database()]:
        influxDB.create_database(db_name)

    # Create retention policies
    retention_names = [r['name'] for r in influxDB.get_list_retention_policies(db_name)]
    if '8weeks' not in retention_names:
        # All raw data is stored for 8 weeks
        influxDB.create_retention_policy(name='8weeks', duration='8w', replication=1, database=db_name, default=True)
    if '26weeks' not in retention_names:
        # All compressed data is stored for 26 weeks (half of a year)
        influxDB.create_retention_policy(name='26weeks', duration='26w', replication=1, database=db_name, default=False)

    # Create continuous queries
    cq_names = [q['name'] for q in [d[db_name] for d in influxDB.get_list_continuous_queries() if db_name in d][0]]
    if 'temp_mean' not in cq_names:
        # downsampling temperature measurements
        select_clause = 'SELECT mean("celsius") AS "mean_celsius" INTO "26weeks"."temps_downsampled" FROM "temps" GROUP BY time(60m), *'
        influxDB.create_continuous_query('temp_mean', select_clause, db_name)
    if 'humid_mean' not in cq_names:
        # downsampling humidity measurements
        select_clause = 'SELECT mean("humidity") AS "mean_humidity" INTO "26weeks"."humids_downsampled" FROM "humids" GROUP BY time(60m), *'
        influxDB.create_continuous_query('humid_mean', select_clause, db_name)
    # downsampling for bat_levels is not needed as they are not quiet frequent, and they should stored to 26weeks by default
    influxDB.switch_database(db_name)


setup_database()


def start_async_worker():  # pragma: no cover
    def _async_worker(msg_queue):
        global influxDB
        while True:
            body, time_precision, retention_policy = msg_queue.get()
            try:
                influxDB.write_points(body, time_precision=time_precision, retention_policy=retention_policy)
            except Exception as e:
                print(f"InfluxDB Connector Error: {e}")

    global async_queue
    global async_process
    if async_process is None:
        async_process = Process(target=_async_worker, args=(async_queue, ), daemon=True)
        async_process.start()


def is_connected():
    global influxDB
    try:
        influxDB.ping()
        return True
    except Exception:  # pragma: no cover
        return False


def _write_points_async(body, time_precision=None, retention_policy=None):
    global async_queue
    async_queue.put((body, time_precision, retention_policy))


def temp_store(celsius, sensor_id, ts, sensor_desc=None, brick_id=None, brick_desc=None):
    global influxDB
    # store to default (8weeks) to temps
    body = {'measurement': 'temps', 'tags': {'sensor_id': sensor_id}, 'time': int(ts), 'fields': {'celsius': float(celsius)}}
    if sensor_desc is not None and not sensor_desc == '':
        body['tags']['sensor_desc'] = sensor_desc
    if brick_id is not None and not brick_id == '':
        body['tags']['brick_id'] = brick_id
    if brick_desc is not None and not brick_desc == '':
        body['tags']['brick_desc'] = brick_desc
    body = [body]
    _write_points_async(body, time_precision='s')


def temp_delete(sensor_id):
    """
    Deletes all temp measurements for a given sensor_id
    """
    global influxDB
    influxDB.delete_series(measurement='temps', tags={'sensor_id': sensor_id})
    influxDB.delete_series(measurement='temps_downsampled', tags={'sensor_id': sensor_id})


def humid_store(humidity, sensor_id, ts, sensor_desc=None, brick_id=None, brick_desc=None):
    global influxDB
    # store to default (8weeks) to humids
    body = {'measurement': 'humids', 'tags': {'sensor_id': sensor_id}, 'time': int(ts), 'fields': {'humidity': float(humidity)}}
    if sensor_desc is not None and not sensor_desc == '':
        body['tags']['sensor_desc'] = sensor_desc
    if brick_id is not None and not brick_id == '':
        body['tags']['brick_id'] = brick_id
    if brick_desc is not None and not brick_desc == '':
        body['tags']['brick_desc'] = brick_desc
    body = [body]
    _write_points_async(body, time_precision='s')


def humid_delete(sensor_id):
    """
    Deletes all humid measurements for a given sensor_id
    """
    global influxDB
    influxDB.delete_series(measurement='humids', tags={'sensor_id': sensor_id})
    influxDB.delete_series(measurement='humids_downsampled', tags={'sensor_id': sensor_id})


def bat_level_store(voltage, v_diff, runtime_prediction, brick_id, ts, brick_desc=None):
    global influxDB
    # store to 26weeks to bat_levels
    body = {'measurement': 'bat_levels', 'tags': {'brick_id': brick_id}, 'time': int(ts), 'fields': {}}
    body['fields']['voltage'] = float(voltage)
    body['fields']['runtime_prediction'] = (float(runtime_prediction) if runtime_prediction else 0.0)
    body['fields']['voltage_diff'] = (float(v_diff) if v_diff else 0.0)
    if brick_desc is not None and not brick_desc == '':
        body['tags']['brick_desc'] = brick_desc
    body = [body]
    _write_points_async(body, time_precision='s', retention_policy='26weeks')


def bat_charging_store(charging, charging_standby, brick_id, ts, brick_desc=None):
    global influxDB
    # store to 26weeks to bat_charging
    body = {'measurement': 'bat_charging', 'tags': {'brick_id': brick_id}, 'time': int(ts), 'fields': {}}
    body['fields']['charging'] = (1 if charging else 0)
    body['fields']['charging_standby'] = (1 if charging_standby else 0)
    if brick_desc is not None and not brick_desc == '':
        body['tags']['brick_desc'] = brick_desc
    body = [body]
    _write_points_async(body, time_precision='s', retention_policy='26weeks')


def bat_stats_delete(brick_id):
    """
    Deletes all bat_level and bat_charging measurements for a given brick_id
    """
    global influxDB
    influxDB.delete_series(measurement='bat_levels', tags={'brick_id': brick_id})
    influxDB.delete_series(measurement='bat_charging', tags={'brick_id': brick_id})


def latch_store(state, latch_id, ts, latch_desc=None, brick_desc=None):
    global influxDB
    # store to default (8weeks) to latches
    brick_id, lid = latch_id.split('_')
    body = {'measurement': 'latches', 'tags': {'latch_id': str(int(lid)), 'brick_id': brick_id}, 'time': int(ts), 'fields': {'state': int(state)}}
    if latch_desc is not None and not latch_desc == '':
        body['tags']['latch_desc'] = latch_desc
    if brick_desc is not None and not brick_desc == '':
        body['tags']['brick_desc'] = brick_desc
    body = [body]
    _write_points_async(body, time_precision='s')


def latch_delete(brick_id, latch_id):
    """
    Deletes all latches measurements of a given latch
    """
    global influxDB
    influxDB.delete_series(measurement='latches', tags={'brick_id': brick_id, 'latch_id': str(int(latch_id))})
