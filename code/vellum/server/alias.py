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

def resolve(actor, words, parsed_dice=None, target=None):
    rolled = getResult(actor, words, parsed_dice, target)
    if rolled is None:
        return None
    else:
        return formatAlias(actor, words, rolled, parsed_dice)

def getResult(actor, words, parsed_dice=None, target=None):
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
        rolled = list(dice.roll(parsed_dice))
    callAliasHooks(words, actor, rolled)
    return rolled

def callAliasHooks(words, user, rolled):
    hooks = alias_hooks.get(words, [])
    for hook in hooks:
        hook(user, rolled)

def test_getResult():
    global aliases
    orig_aliases = aliases
    aliases = {}
    try:
        # junk
        assert getResult('anything', 'foo') is None
        _exp = linesyntax.dice.parseString('1d1')
        assert getResult('anything', 'foo', _exp)  == [1]
        assert getResult('anything', 'bar') is None
        _exp = linesyntax.dice.parseString('500')
        assert getResult('anything', 'bar', _exp) == [500]
        assert getResult('anything', 'bar') == [500]
        assert getResult('anything', 'foo') == [1]
        _exp = linesyntax.dice.parseString('5')
        assert getResult('anything', 'foo', _exp) == [5]
        assert getResult('anything', 'foo') == [5]
    finally:
        aliases = orig_aliases



def formatAlias(actor, verbs, result, parsed_dice, target=None):
    assert target is None
    sorted = 0 
    verbs = list(verbs)
    if parsed_dice is None or parsed_dice == '':
        pass
    else:
        verbs.append(linesyntax.reverseFormatDice(parsed_dice))
        if parsed_dice.dice_sorted:
            result.sort()
            sorted = 1
    rolls = '[%s]' % (', '.join(map(str, result)))
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
    result = [10, 15, 5]
    fmtd = formatAlias(a, v1, result[:], parsed_dice)
    assert (fmtd == 'foobie bletch, you rolled: foo bar 1d20x3 = [10, 15, 5]'),\
            fmtd

    fmtd = formatAlias(a, v2, result[:], parsed_dice) 
    assert (fmtd == 'foobie bletch, you rolled: 1d20x3 = [10, 15, 5]'), \
            fmtd
    fmtd = formatAlias(a, v3, result[:], parsed_dice) 
    assert (fmtd == 'foobie bletch, you rolled: foo 1d20x3 = [10, 15, 5]'), \
            fmtd
    fmtd = formatAlias(a, v3, result[:], parsed_dice3) 
    assert (fmtd == 'foobie bletch, you rolled: foo = [10, 15, 5]'), \
            fmtd
    fmtd = formatAlias(a, v2, result[:], parsed_dice2) 
    assert (fmtd == 'foobie bletch, you rolled: 1d20x3sort = [5, 10, 15] (sorted)'), \
            fmtd


def test():
    test_formatAlias()
    test_shortFormatAliases()
    test_getResult()
    print 'all tests passed'



def _chewLog(filename):
    """Take a gaim-format irc log and reprocess it, parsing aliases.
    """
    m = (r'^$',
         r'Conversation with \S+',
         r'\(..:..:..\) The topic for \S+ is: \S+',
         r'\(..:..:..\) \S+ \[.*@.*\..*\] entered the room',
         r'\(..:..:..\) \S+ \[.*@.*\..*\] left the room',
         r'\(..:..:..\) \S+ left the room \(quit: .*?\)\.',
         r'\(..:..:..\) \S+ is now known as \S+',
         r'\(..:..:..\) You are now known as \S+',
         r'\(..:..:..\) \S+: \*(?P<nick>\S+) (?P<msg>.*)',
         r'\(..:..:..\) (?P<nick>\S+): (?P<msg>.*)',
         r'\(..:..:..\) \*\*\*(?P<nick>\S+) (?P<msg>\S+)',
         )

    import re
    for line in file(filename, 'rb'):
        line = line.strip()
        # scan to determine whether this line is a privmsg or should be
        # ignored
        for pat in m:
            matched = re.match(pat, line)
            if matched is not None: break
        else:
            # all lines should match one of the above regex's
            assert matched is not None, '"%s"' % (line,)

        # pull out nick and extract expressions from msg, then parse exprs
        nick = matched.groupdict().get('nick', None)
        if nick is not None:
            msg = matched.group('msg')
            for exp in re.findall(r'{.+?}|\[.+?\]', msg):
                print parseAlias(exp[1:-1], nick),
    print
