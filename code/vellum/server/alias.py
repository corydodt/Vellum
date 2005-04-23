"""A table of aliases."""
from vellum.server import dice

roller = dice.Roller()

aliases = {}


def rollSafe(st):
    try:
        return roller.roll(st)
    except RuntimeError, e:
        return None

def test_rollSafe():
    assert type(rollSafe('1 d20 +1')) is type([])
    assert rollSafe('1 d +1') is None


alias_hooks = {}

def registerAliasHook(alias, hook):
    """Register a handler for a particular alias.  Handlers must
    take two arguments, username and evaluated result.

    def rememberInitiative(user, initroll):
        iniatives.append((initroll, user))
    >>> addAliasHook('init', rememberInitiative)

    Now rememberInitiative will get called any time someone uses "{init ..}"
    """
    alias_hooks.setdefault(alias, []).append(hook)


def parseAlias(st, user):
    """Valid syntaxes:
    {anything you want here} => look up entire str on alias table
    {anything <dice_expression>} => assign <dice_expression> to anything
    {<dice_expression>} => dice expression
    """
    # try the whole thing as a dice expression first
    rolled = rollSafe(st)
    if rolled is not None:
        return rolled

    # now it's either an alias reference or an alias assignment or junk
    words = st.split()
    dicetry = words[-1]
    rolled = rollSafe(dicetry)
    if rolled is None:
        # alias or junk. roll it if we can
        expression = aliases.get(user, {}).get(tuple(words), '')
        return rollSafe(expression)
    else:
        # alias assignment
        aliases.setdefault(user, {})[tuple(words[:-1])] = dicetry 
        return rolled

def test_parseAlias():
    # junk
    assert parseAlias('anything', 'foo') is None
    assert parseAlias('anything 1d1', 'foo')  == [1]
    assert parseAlias('anything 1d 1', 'foo') == [1]
    assert parseAlias('1 d 1', 'foo') == [1]
    assert parseAlias('anything', 'bar') is None
    assert parseAlias('anything 500', 'bar') == [500]
    assert parseAlias('anything', 'bar') == [500]
    assert parseAlias('anything', 'foo') == [1]
    assert parseAlias('anything 5', 'foo') == [5]
    assert parseAlias('anything', 'foo') == [5]
        

def resolve(user, alias):
    if alias[0] == '[':
        sorted = 1
    else:
        sorted = 0
    alias = alias.strip('{}[]')

    rolled = parseAlias(alias, user)
    for alias in alias_hooks:
        for hook in alias_hooks[alias]:
            hook(user, rolled)

    if rolled is not None:
        return '%s = %s' % (alias, formatDice(rolled, sorted))

def test_resolve():
    try:
        resolve('foo', '')
    except IndexError:
        pass
    assert resolve('foo', '[xyz]') is None
    assert resolve('foo', '{1d1}') == '1d1 = {1}'
    assert resolve('foo', '[1 d1]') == '1 d1 = [1]'
    remember = 'xyz 1d1x5 = [1, 1, 1, 1, 1] (sorted)'
    assert resolve('foo', '[xyz 1d1x5]'
                   ) == remember
    assert resolve('foo', '[xyz 1d 1]') == 'xyz 1d 1 = [1]'
    assert resolve('foo', '{xyz }') == 'xyz  = {1, 1, 1, 1, 1}'
    assert resolve('foo', '[ xyz]') == ' xyz = [1, 1, 1, 1, 1] (sorted)'


def formatDice(rolls, sorted):
    if sorted:
        rolls.sort()
        rolls = map(str, rolls)
        _roll = '[%s]' % (', '.join(rolls),)
        if len(rolls) > 1:
            _roll = _roll + ' (sorted)'
    else:
        rolls = map(str, rolls)
        _roll = '{%s}' % (', '.join(rolls),)
    return _roll

def test_formatDice():
    assert formatDice([1,2,3,2], 0) == '{1, 2, 3, 2}'
    assert formatDice([1,2,3,2], 1) == '[1, 2, 2, 3] (sorted)'
    assert formatDice([], 1) == '[]'
    try:
        formatDice(None, 1)
    except AttributeError:
        pass


def test():
    test_rollSafe()
    test_resolve()
    test_formatDice()
    test_parseAlias()
    print 'all tests passed'

