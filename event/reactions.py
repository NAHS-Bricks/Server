import requests
import json
from helpers.mongodb import brick_get, event_data_get, event_data_save


def __call_admin_interface(data):
    if isinstance(data, str):  # pragma: no cover
        data = json.loads(data)
    from helpers.admin import admin_interface
    return admin_interface(data)


def _set_signal_state(event, event_data):
    for requirement in ['signal_id', 'state']:
        if requirement not in event_data:
            return False
    data = {
        'command': 'get_signal',
        'signal': event_data['signal_id']
    }
    if __call_admin_interface(data)['signal']['state'] == int(event_data['state']):
        return True  # if signal allready in desired state there is no need to set it again
    data = {
        'command': 'set',
        'key': 'signal',
        'signal': event_data['signal_id'],
        'value': int(event_data['state'])
    }
    return __call_admin_interface(data)['s'] == 0


def _trigger_brick(event, event_data):
    if 'brick' not in event_data:
        return False
    brick = brick_get(event_data['brick'])
    if 'sleep' in brick['features']:
        return False  # trigger not possible as brick is sleeping
    rs = requests.Session()
    rs.headers = {'Content-Type': 'application/json'}
    try:
        rs.post(f"http://{brick['ip']}/", data={}, timeout=2)
    except Exception:
        pass
    return True


def _math(event, event_data):
    for requirement in ['operator', 'operand', 'event_data_name', 'event_data_key']:
        if requirement not in event_data:
            return False
    ed = event_data_get(event, event_data['event_data_name'])
    if event_data['event_data_key'] not in ed:
        ed[event_data['event_data_key']] = 0
    try:
        if event_data['operator'] == '=':
            ed[event_data['event_data_key']] = event_data['operand']
        elif event_data['operator'] == '+':
            ed[event_data['event_data_key']] += event_data['operand']
        elif event_data['operator'] == '-':
            ed[event_data['event_data_key']] -= event_data['operand']
        elif event_data['operator'] == '*':
            ed[event_data['event_data_key']] *= event_data['operand']
        elif event_data['operator'] == '/':
            ed[event_data['event_data_key']] /= event_data['operand']
        elif event_data['operator'] == '%':
            ed[event_data['event_data_key']] %= event_data['operand']
        else:
            return False
    except Exception:
        return False  # invalid operand
    event_data_save(ed)
    return True


reactions = {
    'set_signal_state': _set_signal_state,
    'trigger_brick': _trigger_brick,
    'math': _math
}
