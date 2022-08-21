from connector.mongodb import signal_all, signal_save, latch_get, fanctl_all, fanctl_save
from connector.mqtt import signal_send, fanctl_state_send, fanctl_duty_send
from connector.influxdb import signal_store, fanctl_duty_store


def feedback_exec(brick, process_requests=list(), feature_requests=list(), by_activator=False):
    result = {'s': 0}

    """
    What the following line does:
    Takes all entrys from process_requests + feature_requests and:
      - drops None elements
      - makes non list items to lists with one item aka if type(item) is not list return [item]
      - passes trough all lists
    this results in a list of lists, each of this lists is then unpacked in to one big list with all elements
    with the use of {} duplicate elements are removed
    """
    for k in {x for t in [(p if type(p) is list else [p]) for p in process_requests + feature_requests if p] for x in t}:
        if k.startswith('request_') and 'r' not in result:
            result['r'] = []
        if k == 'update_delay':
            result['d'] = brick['delay']
        elif k == 'update_sleep_disabled':
            result['q'] = brick['sleep_set_disabled']
        elif k == 'update_temp_precision':
            result['p'] = brick['temp_precision']
        elif k == 'update_bat_adc5V':
            result['a'] = brick['bat_adc5V']
        elif k == 'update_latch_triggers':
            result['t'] = list()
            for i in range(0, brick['latch_count']):
                result['t'].append(sorted(latch_get(brick['_id'], i)['triggers']))
        elif k == 'update_signal_states':
            result['o'] = list()
            for signal in signal_all(brick['_id']):
                result['o'].append(signal['state'])
                if not by_activator:
                    if signal['state_transmitted_ts'] is None:
                        signal['state_transmitted_ts'] = brick['last_ts']
                        signal_save(signal)
                    if 'mqtt' not in signal['disables']:
                        signal_send(signal['_id'], signal['state'], True)
                    if 'metric' not in signal['disables']:
                        signal_store(state=signal['state'], signal_id=signal['_id'], ts=brick['last_ts'], signal_desc=signal['desc'], brick_desc=brick['desc'])
        elif k == 'update_fanctl_mode':
            result['fm'] = list()
            for fanctl in fanctl_all(brick['_id']):
                if fanctl['mode'] is not None and fanctl['mode_transmitted_ts'] is None:
                    result['fm'].append([int(fanctl['_id'].split('_')[1], 16), fanctl['mode']])
                    fanctl['mode_transmitted_ts'] = brick['last_ts']
                    fanctl_save(fanctl)
        elif k == 'update_fanctl_duty':
            result['fd'] = list()
            for fanctl in fanctl_all(brick['_id']):
                if (fanctl['dutyCycle_transmitted_ts'] is None or (not fanctl['state'] == fanctl['state_should'] and fanctl['state_should'] == 1)) and fanctl['dutyCycle'] is not None and fanctl['mode'] is not None and fanctl['mode'] > -1:
                    result['fd'].append([int(fanctl['_id'].split('_')[1], 16), fanctl['dutyCycle']])
                    fanctl['dutyCycle_transmitted_ts'] = brick['last_ts']
                    fanctl_save(fanctl)
                    if 'mqtt' not in fanctl['disables']:
                        fanctl_duty_send(fanctl['_id'], fanctl['dutyCycle'])
                    if 'metric' not in fanctl['disables']:
                        fanctl_duty_store(fanctl['dutyCycle'], fanctl['_id'], brick['last_ts'], fanctl['desc'], brick['desc'])
        elif k == 'update_fanctl_state':
            result['fs'] = list()
            for fanctl in fanctl_all(brick['_id']):
                if fanctl['state_should'] is not None and fanctl['mode'] is not None and fanctl['mode'] > -1:
                    result['fs'].append([int(fanctl['_id'].split('_')[1], 16), fanctl['state_should']])
                    if 'mqtt' not in fanctl['disables']:
                        fanctl_state_send(fanctl['_id'], fanctl['state_should'], received=False)
        elif k == 'request_versions':
            result['r'].append(1)
        elif k == 'request_bat_voltage':
            result['r'].append(3)
        elif k == 'request_temp_corr':
            result['r'].append(4)
        elif k == 'request_type':
            result['r'].append(5)
        elif k == 'request_temp_precision':
            result['r'].append(6)
        elif k == 'request_signal_count':
            result['r'].append(7)
        elif k == 'request_delay_default':
            result['r'].append(8)
        elif k == 'request_humid_corr':
            result['r'].append(9)
        elif k == 'request_bat_adc5V':
            result['r'].append(10)
        elif k == 'request_sketchMD5':
            result['r'].append(11)
        elif k == 'request_otaUpdate':
            result['r'].append(12)
        elif k == 'request_fanctl_mode':
            result['r'].append(13)

    # special-case: requests are made and feature sleep is present or all is at least v1.02: override delay to 10 -- except admin_override for delay is present or delay_overwrite is True
    if 'r' in result and ('admin_override' not in brick or 'delay' not in brick['admin_override']) and ('sleep' in brick['features'] or brick['features']['all'] >= 1.02) and not (brick['features']['all'] >= 1.02 and brick['delay_overwrite']):
        brick['delay'] = 10
        result['d'] = 10

    if by_activator:  # pragma: no cover
        result.pop('d', None)  # delays are not allowed to be send on activator feedback, as this could lead to problems

    return result
