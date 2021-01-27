from influxdb import InfluxDBClient
from helpers.shared import config
import json
from datetime import datetime

influxDB = InfluxDBClient(host=config['influx']['server'], port=int(config['influx']['port']))


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

    # Create continous queries
    cq_names = [q['name'] for q in [d[db_name] for d in influxDB.get_list_continuous_queries() if db_name in d][0]]
    if 'temp_mean' not in cq_names:
        # downsampling temperature measurements
        select_clause = 'SELECT mean("celsius") AS "mean_celsius" INTO "26weeks"."temps_downsampled" FROM "temps" GROUP BY time(60m), *'
        influxDB.create_continuous_query('temp_mean', select_clause, db_name)
    # downsampling for bat_levels is not needed as they are not quiet frequent, and they should stored to 26weeks by default
    influxDB.switch_database(db_name)


setup_database()


def temp_store(celsius, sensor_id, ts):
    global influxDB
    # store to default (8weeks) to temps
    body = [{'measurement': 'temps', 'tags': {'sensor_id': sensor_id}, 'time': int(ts), 'fields': {'celsius': float(celsius)}}]
    influxDB.write_points(body, time_precision='s')


def bat_level_store(voltage, charging, charging_standby, brick_id, ts):
    global influxDB
    # store to 26weeks to bat_levels
    dt = datetime.fromtimestamp(ts).isoformat(timespec='seconds') + 'Z'
    body = [{'measurement': 'bat_levels', 'tags': {'brick_id': brick_id}, 'time': int(ts), 'fields': {'voltage': float(voltage), 'charging': (1 if charging else 0), 'charging_standby': (1 if charging_standby else 0)}}]
    influxDB.write_points(body, time_precision='s', retention_policy='26weeks')
