from connector.mongodb import signal_all, latch_get


def _signals_pending(event, event_data, brick, brick_old):
    if 'admin_override' in brick['features'] and 'admin_override' in brick and 'signal_states' in brick['admin_override'] and brick['admin_override']['signal_states']:
        return True
    return False


def _latch_state_match(event, event_data, brick, brick_old):
    def eval(expression):
        if not isinstance(expression, list):
            if isinstance(expression, str):
                return latch_get(brick['_id'], expression)['last_state']
            return expression
        if not len(expression) == 3:
            return False

        if expression[1] == '==':
            return eval(expression[0]) == eval(expression[2])
        elif expression[1] == '!=':
            return not eval(expression[0]) == eval(expression[2])
        elif expression[1] == 'and':
            return eval(expression[0]) and eval(expression[2])
        elif expression[1] == 'or':
            return eval(expression[0]) or eval(expression[2])
        elif expression[1] == '>':
            return eval(expression[0]) > eval(expression[2])
        elif expression[1] == '<':
            return eval(expression[0]) < eval(expression[2])
        elif expression[1] == '>=':
            return eval(expression[0]) >= eval(expression[2])
        elif expression[1] == '<=':
            return eval(expression[0]) <= eval(expression[2])
        else:
            return False

    if 'latch' not in brick['features']:
        return False
    if 'expression' not in event_data or not isinstance(event_data['expression'], list):
        return False

    return eval(event_data['expression'])


commands = {
    'signals_pending': _signals_pending,
    'latch_state_match': _latch_state_match
}
