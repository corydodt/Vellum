"""A table of aliases."""
try:
    import cPickle as pickle
except ImportError:
    import pickle
import atexit
import errno

from twisted.python import log

from vellum.server import dice, linesyntax
from vellum.server.fs import fs

aliases = {}

def saveAliases():
    log.msg('saving aliases')
    pickle.dump(aliases, 
                file(fs.aliases('aliases.pkl'), 'wb'), 
                2)

def loadAliases():
    try:
        global aliases
        aliases = pickle.load(file(fs.aliases('aliases.pkl'), 'rb'))
        log.msg('loaded aliases')
    except IOError, e:
        # if the file just doesn't exist, assume we have to create it.
        if e.errno == errno.ENOENT:
            log.msg('new aliases.pkl')
        else:
            raise
    except EOFError, e:
        # this indicates file not found as well, not sure why..
        log.msg('new aliases.pkl')

# This is horrible, FIXME
loadAliases()
atexit.register(saveAliases)




alias_hooks = {}

def registerAliasHook(alias, hook):
    """Register a handler for a particular alias.  Handlers must
    take two arguments, username and evaluated result.

    def rememberInitiative(user, initroll):
        iniatives.append((initroll, user))
    >>> addAliasHook(('init',), rememberInitiative)

    Now rememberInitiative will get called any time someone uses "[init ..]"
    """
    alias_hooks.setdefault(alias, []).append(hook)

def removeAlias(st, user):
    user_aliases = aliases.get(user, {})
    key = tuple(st.split())
    return user_aliases.pop(key, None)

def shortFormatAliases(user):
    """Return all the aliases for user in a short format"""
    my_aliases = aliases.get(user, {})
    if len(my_aliases) == 0:
        return '(none)'
    formatted_aliases = []
    alias_items = my_aliases.items()
    alias_items.sort()
    for key, value in alias_items:
        formatted_key = ' '.join(key)
        formatted_aliases.append('%s=%s' % (formatted_key, value))
    return ', '.join(formatted_aliases)

def test_shortFormatAliases():
    global aliases
    orig_aliases = aliases
    aliases = {'foobar': {('buncha', 'crunch'): '2d20+20',
                          ('yums',): '1234'
                          },
               'empty': {},
               }
    try:
        assert shortFormatAliases('foobar') == (
                'buncha crunch=2d20+20, yums=1234')
        assert shortFormatAliases('empty') == '(none)'
        assert shortFormatAliases('NOBODY') == '(none)'
    finally:
        aliases = orig_aliases

def resolve(actor, words, parsed_dice=None, temp_modifier=0, target=None):
    rolled = getResult(actor, words, parsed_dice, temp_modifier, target=target)
    if rolled is None:
        return None
    else:
        return formatAlias(actor, words, rolled, parsed_dice, temp_modifier)

def callAliasHooks(words, user, rolled):
    hooks = alias_hooks.get(words, [])
    for hook in hooks:
        hook(user, rolled)

def getResult(actor, words, parsed_dice=None, temp_modifier=0, target=None):
    """Return a list of dice results"""
    assert target is None # TODO
    parse = linesyntax.dice.parseString
    unparse = linesyntax.reverseFormatDice

    # verb phrases with dice expressions set a new expression
    if parsed_dice:
        aliases.setdefault(actor, {})[words] = unparse(parsed_dice)
        saveAliases()
    else: # without dice expression, look it up or regard it as empty
        _dict = aliases.get(actor, {})
        looked_up = _dict.get(words, None)
        if looked_up is None:
            parsed_dice = None
        else:
            parsed_dice = parse(looked_up)

    if parsed_dice is None:
        rolled = None
    else:
        rolled = list(dice.roll(parsed_dice, temp_modifier))
    callAliasHooks(words, actor, rolled)
    return rolled

def test_getResult():
    global aliases
    orig_aliases = aliases
    aliases = {}
    try:
        # junk
        assert getResult('anything', 'foo') is None
        # define an alias
        _exp = linesyntax.dice.parseString('1d1')
        assert getResult('anything', 'foo', _exp)[0].sum() == 1
        # junk after defining real aliases
        assert getResult('anything', 'bar') is None
        _exp = linesyntax.dice.parseString('500')
        # define and recall an alias
        assert getResult('anything', 'bar', _exp)[0].sum() == 500
        assert getResult('anything', 'bar')[0].sum() == 500
        # recall the first alias
        assert getResult('anything', 'foo')[0].sum() == 1
        _exp = linesyntax.dice.parseString('5')
        # redefine and recall an alias
        assert getResult('anything', 'foo', _exp)[0].sum() == 5
        assert getResult('anything', 'foo')[0].sum() == 5
        # temp modifier
        assert getResult('anything', 'foo', None, -1)[0].sum() == 4
    finally:
        aliases = orig_aliases



def formatAlias(actor, 
                verbs, 
                results, 
                parsed_dice, 
                temp_modifier=0, 
                target=None):
    assert target is None
    sorted = 0 
    verbs = list(verbs)
    if parsed_dice is None or parsed_dice == '':
        pass
    else:
        verbs.append(linesyntax.reverseFormatDice(parsed_dice))
        # use 'sort' token to decide whether to sort now
        if parsed_dice.dice_sorted:
            results.sort()
            sorted = 1
    if temp_modifier:
        verbs.append('%+d' % (temp_modifier,))

    
    rolls = '[%s]' % (', '.join([r.format() for r in results]))
    if sorted:
        rolls = rolls + ' (sorted)'
    return '%s, you rolled: %s = %s' % (actor, ' '.join(verbs), rolls)

def test_formatAlias():
    a = 'foobie bletch'
    v1 = ['foo', 'bar']
    v2 = []
    v3 = ['foo']
    parsed_dice = linesyntax.dice_string.parseString('1d20x3')
    parsed_dice2 = linesyntax.dice_string.parseString('1d20x3sort')
    parsed_dice3 = ''
    parsed_dice4 = linesyntax.dice_string.parseString('3d6+2')

    R = lambda n: dice.DiceResult([n], 0)
    results = [R(10), R(15), R(5)]
    results2 = [dice.DiceResult([3,4,5], 2)]
    results3 = [dice.DiceResult([3,4,5], 2, 2)]

    fmtd = formatAlias(a, v1, results[:], parsed_dice)
    assert (fmtd == 'foobie bletch, you rolled: foo bar 1d20x3 = [10, 15, 5]'),\
            fmtd

    fmtd = formatAlias(a, v2, results[:], parsed_dice) 
    assert (fmtd == 'foobie bletch, you rolled: 1d20x3 = [10, 15, 5]'), \
            fmtd
    fmtd = formatAlias(a, v3, results[:], parsed_dice) 
    assert (fmtd == 'foobie bletch, you rolled: foo 1d20x3 = [10, 15, 5]'), \
            fmtd
    fmtd = formatAlias(a, v3, results[:], parsed_dice3) 
    assert (fmtd == 'foobie bletch, you rolled: foo = [10, 15, 5]'), \
            fmtd
    fmtd = formatAlias(a, v2, results[:], parsed_dice2) 
    assert (fmtd == 'foobie bletch, you rolled: 1d20x3sort = [5, 10, 15] (sorted)'), \
            fmtd
    fmtd = formatAlias(a, v2, results2[:], parsed_dice4) 
    assert (fmtd == 'foobie bletch, you rolled: 3d6+2 = [3+4+5+2 = 14]'), \
            fmtd
    fmtd = formatAlias(a, v2, results3[:], parsed_dice4, 2) 
    assert (fmtd == 'foobie bletch, you rolled: 3d6+2 +2 = [3+4+5+2+2 = 16]'), \
            fmtd


def test():
    test_formatAlias()
    test_shortFormatAliases()
    test_getResult()
    print 'all tests passed'



if __name__ == '__main__':
    test()
