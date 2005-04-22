"""A table of aliases."""
from vellum.server import dice

roller = dice.Roller()

aliases = {}


def resolve(user, alias):
    if alias[0] == '[':
        sorted = 1
    else:
        sorted = 0
    alias = alias.strip('{}[]')
    try:
        roll = roller.roll(alias)
        if sorted:
            roll.sort()
            roll = map(str, roll)
            _roll = '[%s]' % (', '.join(roll),)
            if len(roll) > 1:
                _roll = _roll + ' (sorted)'
        else:
            roll = map(str, roll)
            _roll = '{%s}' % (', '.join(roll),)
        return '%s = %s' % (alias, _roll)
    except RuntimeError, e:
        return None
