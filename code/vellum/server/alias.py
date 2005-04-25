"""A table of aliases."""
try:
    import cPickle as pickle
except ImportError:
    import pickle
import atexit
import errno

from vellum.server import dice
from vellum.server.fs import fs

roller = dice.Roller()

aliases = {}

def saveAliases():
    print 'saving aliases'
    pickle.dump(aliases, 
                file(fs.aliases('aliases.pkl'), 'wb'), 
                2)

def loadAliases():
    try:
        aliases = pickle.load(file(fs.aliases('aliases.pkl'), 'rb'))
        print 'loaded aliases'
    except IOError, e:
        # if the file just doesn't exist, assume we have to create it.
        if e.errno == errno.ENOENT:
            print 'new aliases.pkl'
        else:
            raise


loadAliases()
atexit.register(saveAliases)


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
    >>> addAliasHook(('init',), rememberInitiative)

    Now rememberInitiative will get called any time someone uses "[init ..]"
    """
    alias_hooks.setdefault(alias, []).append(hook)


def parseAlias(st, user):
    """Valid syntaxes:
    [anything you want here] => look up entire str on alias table
    [anything <dice_expression>] => assign <dice_expression> to anything
    [<dice_expression>] => dice expression
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
        words = tuple(words)
        expression = aliases.get(user, {}).get(words, '')
        rolled = rollSafe(expression)
    else:
        # alias assignment
        words = tuple(words[:-1])
        aliases.setdefault(user, {})[words] = dicetry
        saveAliases()
    callAliasHooks(words, user, rolled)
    return rolled

def callAliasHooks(words, user, rolled):
    hooks = alias_hooks.get(words, [])
    for hook in hooks:
        hook(user, rolled)

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
    if alias[0] == '{':
        sorted = 1
    else:
        sorted = 0
    alias = alias.strip('[]{}')

    rolled = parseAlias(alias, user)

    if rolled is not None:
        return '%s = %s' % (alias, formatDice(rolled, sorted))

def test_resolve():
    try:
        resolve('foo', '')
    except IndexError:
        pass
    assert resolve('foo', '{xyz}') is None
    assert resolve('foo', '[1d1]') == '1d1 = [1]'
    assert resolve('foo', '{1 d1}') == '1 d1 = {1}'
    remember = 'xyz 1d1x5 = {1, 1, 1, 1, 1} (sorted)'
    assert resolve('foo', '{xyz 1d1x5}'
                   ) == remember
    assert resolve('foo', '{xyz 1d 1}') == 'xyz 1d 1 = {1}'
    assert resolve('foo', '[xyz ]') == 'xyz  = [1, 1, 1, 1, 1]'
    assert resolve('foo', '{ xyz}') == ' xyz = {1, 1, 1, 1, 1} (sorted)'


def formatDice(rolls, sorted):
    if sorted:
        rolls.sort()
        rolls = map(str, rolls)
        _roll = '{%s}' % (', '.join(rolls),)
        if len(rolls) > 1:
            _roll = _roll + ' (sorted)'
    else:
        rolls = map(str, rolls)
        _roll = '[%s]' % (', '.join(rolls),)
    return _roll

def test_formatDice():
    assert formatDice([1,2,3,2], 0) == '[1, 2, 3, 2]'
    assert formatDice([1,2,3,2], 1) == '{1, 2, 2, 3} (sorted)'
    assert formatDice([], 1) == '{}'
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
