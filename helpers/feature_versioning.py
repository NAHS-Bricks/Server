
def _all_initial(brick):
    if 'type' not in brick:
        brick['type'] = None
    if 'features' not in brick:
        brick['features'] = dict()
        brick['features']['all'] = 0
        brick['features']['os'] = 0
    if 'desc' not in brick:
        brick['desc'] = ''
    if 'last_ts' not in brick:
        brick['last_ts'] = None
    if 'initalized' not in brick:
        brick['initalized'] = False


def _temp_initial(brick):
    if 'temp_sensors' not in brick:
        brick['temp_sensors'] = list()
    if 'temp_precision' not in brick:
        brick['temp_precision'] = None
    if 'temp_max_diff' not in brick:
        brick['temp_max_diff'] = 0


def _bat_initial(brick):
    if 'bat_last_reading' not in brick:
        brick['bat_last_reading'] = 0
    if 'bat_last_ts' not in brick:
        brick['bat_last_ts'] = None
    if 'bat_charging' not in brick:
        brick['bat_charging'] = False
    if 'bat_charging_standby' not in brick:
        brick['bat_charging_standby'] = False
    if 'bat_periodic_voltage_request' not in brick:
        brick['bat_periodic_voltage_request'] = 10


def _sleep_initial(brick):
    if 'sleep_delay' not in brick:
        brick['sleep_delay'] = 60
    if 'sleep_increase_wait' not in brick:
        brick['sleep_increase_wait'] = 3


def _latch_initial(brick):
    if 'latch_states' not in brick:
        brick['latch_states'] = list()
    if 'latch_triggers' not in brick:
        brick['latch_triggers'] = list()


_feature_updates = {
    'all': {
        0.00: _all_initial
    },
    'os': {},
    'temp': {
        0.00: _temp_initial
    },
    'bat': {
        0.00: _bat_initial
    },
    'sleep': {
        0.00: _sleep_initial
    },
    'latch': {
        0.00: _latch_initial
    }
}


def feature_update(brick, feature, from_version, to_version):
    if feature in _feature_updates:
        for version in sorted(_feature_updates[feature].keys()):
            if version >= from_version and version <= to_version:
                _feature_updates[feature][version](brick)


def features_available():
    return list(_feature_updates.keys())
