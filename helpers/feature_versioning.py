
def _all_initial(brick):
    brick['type'] = None
    brick['features'] = dict()
    brick['features']['all'] = 0
    brick['features']['os'] = 0
    brick['desc'] = None
    brick['init_ts'] = None
    brick['last_ts'] = None
    brick['initalized'] = False
    brick['ip'] = None
    brick['delay'] = 60


def _all_102(brick):
    brick['delay_default'] = None
    brick['delay_overwrite'] = False


def _os_101(brick):
    brick['sketchMD5'] = None


def _temp_initial(brick):
    brick['temp_sensors'] = list()
    brick['temp_precision'] = None
    brick['temp_max_diff'] = 0


def _humid_initial(brick):
    brick['humid_sensors'] = list()
    brick['humid_max_diff'] = 0


def _bat_initial(brick):
    brick['bat_last_reading'] = 0
    brick['bat_last_ts'] = None
    brick['bat_charging'] = False
    brick['bat_charging_standby'] = False
    brick['bat_periodic_voltage_request'] = 10
    brick['bat_solar_charging'] = False
    brick['bat_init_ts'] = None
    brick['bat_init_voltage'] = None
    brick['bat_runtime_prediction'] = None


def _bat_101(brick):
    brick['bat_adc5V'] = None


def _sleep_initial(brick):
    brick['sleep_increase_wait'] = 3


def _sleep_101(brick):
    brick['sleep_disabled'] = False
    brick['sleep_set_disabled'] = None


def _latch_initial(brick):
    brick['latch_count'] = 0
    brick['latch_triggerstate_received'] = False


def _signal_initial(brick):
    brick['signal_count'] = None


_feature_updates = {
    'all': {
        0.00: _all_initial,
        1.02: _all_102
    },
    'os': {
        1.01: _os_101
    },
    'sleep': {
        0.00: _sleep_initial,
        1.01: _sleep_101
    },
    'bat': {
        0.00: _bat_initial,
        1.01: _bat_101
    },
    'temp': {
        0.00: _temp_initial
    },
    'heat': {
        0.00: _temp_initial
    },
    'humid': {
        0.00: _humid_initial
    },
    'latch': {
        0.00: _latch_initial
    },
    'signal': {
        0.00: _signal_initial
    }
}


def feature_update(brick, feature, from_version, to_version):
    if from_version < to_version and feature in _feature_updates:
        for version in sorted(_feature_updates[feature].keys()):
            if version > from_version and version <= to_version:
                _feature_updates[feature][version](brick)


def features_available():
    return list(_feature_updates.keys())
