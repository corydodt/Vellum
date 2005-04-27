"""
Vellum's face.  The bot that answers actions in the channel.
"""
# system imports
import time, sys
import re
import traceback
import glob

# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, task
from twisted.python import log


from vellum.server import encounter, alias
from vellum.server.fs import fs


class VellumTalk(irc.IRCClient):
    """An irc boy that handles D&D game sessions.
    (Currently contains d20-specific assumption about initiative.)
    """
    
    nickname = "VellumTalk"

    def __init__(self, *args, **kwargs):
        self.encounters = []
        self.party = encounter.Encounter()
        self.wtf = 0  # number of times a "wtf" has occurred recently.
        # reset wtf's every 30 seconds 
        self.resetter = task.LoopingCall(self._resetWtfCount).start(30.0)

        self.responding = 0 # don't start responding until i'm in a channel
        self.club = encounter.Club()
        self._loadParty()
        # TODO - move this into d20-specific code somewhere
        self.initiatives = []
        alias.registerAliasHook(('init',), self.doInitiative)
        # irc.IRCClient.__init__(self, *args, **kwargs)

    def _loadParty(self):
        """Load characters in the party/ dir"""
        for filename in glob.glob(fs.party('*.yml')):
            char = encounter.Character(filename=fs.party(filename))
            self.party.addCharacter(char)
    
    def connectionMade(self):
        irc.IRCClient.connectionMade(self)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)


    def doInitiative(self, user, result):
        self.initiatives.append((result[0], user))
        self.initiatives.sort()
        self.initiatives.reverse()


    # callbacks for events

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.join(self.factory.channel)

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        self.responding = 1

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]
        log.msg(user, channel, msg)
        if not self.responding:
            return
        # Check to see if they're sending me a private message
        # If so, the return channel is the user.
        # This also reminds us that private messages are always commands.
        if channel == self.nickname:
            channel = user

        # if the line begins with *foo, then I am talking as foo, and
        # foo should be considered the user
        if msg.startswith('*'):
            first = msg.split()[0]
            name = first[1:]
            if len(name) > 0:
                user = name

        # if the bot is being addressed, do stuff
        _re = r'^(%s:) |^(\.)' % (self.nickname,)
        _hail = re.compile(_re, re.I)
        match = _hail.search(msg)
        if match is not None:
            command = msg[match.end():]
            return self.dispatchCommand(channel, user, command)
        if channel == user:
            return self.dispatchCommand(channel, user, msg)

        # dice are handled if the bot is not being addressed
        return self._handleDice(channel, user, msg)

    def _handleDice(self, channel, user, msg):
        dice_expressions = re.findall(r'\[.+?\]|{.+?}', msg)
        for exp in dice_expressions:
            self.respondTo_DICE(channel, user, exp)

    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        user = user.split('!', 1)[0]
        log.msg(user, channel, msg)
        if not self.responding:
            return
        if channel == self.nickname:
            channel = user

        # only dice are handled in actions
        return self._handleDice(channel, user, msg)

    def dispatchCommand(self, channel, user, command):
        """Choose a method based on the command word, and pass args if any"""
        command_word = 'DEFAULT'
        args = None
        if command:
            _splits = command.split(None, 1)
            command_word = _splits.pop(0)
            if len(_splits) > 0:
                args = _splits[0]
        m = getattr(self, 'respondTo_%s' % (command_word,), 
                    self.respondTo_DEFAULT)
        # try harder to find dice expressions when there's no command
        if m == self.respondTo_DEFAULT:
            if re.search(r'\[.+?\]|{.+?}', command) is not None:
                return self._handleDice(channel, user, command)
        try:
            m(channel, user, args)
        except Exception, e:
            self.msg(channel, '** Sorry, %s: %s' % (user, str(e)))
            log.msg(''.join(traceback.format_exception(*sys.exc_info())))


    # responses to being hailed by a user

    def respondTo_DEFAULT(self, channel, user, args):
        # we don't want to get caught looping, so respond up to 3 times
        # with wtf, then wait for the counter to reset
        if self.wtf < 3:
            self.msg(channel, "wtf?")
            self.wtf = self.wtf + 1
            return
        if self.wtf < 4:
            print "Spam blocking tripped. WTF counter exceeded."
            self.wtf = self.wtf + 1

    def _resetWtfCount(self):
        self.wtf = 0

    def respondTo_DICE(self, channel, user, exp):
        """{d1ce} expressions
        Understands all the expressions in dice.py
        Also understands aliases, for example:
        <bob> {battleaxe 1d20+3} => rolls 1d20+3, and remembers that bob's
            alias {battleaxe} is 1d20+3
        When defining an alias, the dice expression must not contain spaces
        """
        result = alias.resolve(user, exp)
        if result is not None:
            response = '%s, you rolled: %s' % (user, result)
            self.msg(channel, response)

    def respondTo_hello(self, channel, user, _):
        """Greet."""
        self.msg(channel, 'Hello %s.' % (user,))

    def respondTo_n(self, channel, user, _):
        """Next initiative"""
        next = self.initiatives.pop(0)
        if next[1] is None:
            self.msg(channel, '++ New round ++')
            # TODO - update timed events here (don't update on prev init)
        else:
            self.msg(channel, '%s (init %s) is ready to act . . .' % (next[1], 
                                                                      next[0],))
        self.initiatives.append(next)

    def respondTo_p(self, channel, user, _):
        """Previous initiative"""
        last, prev = self.initiatives.pop(-1), self.initiatives.pop(-1)
        if prev[1] is None:
            self.msg(channel, '++ New round ++')
        else:
            self.msg(channel, 
                     '%s (init %s) is ready to act . . .' % (prev[1], 
                                                             prev[0],))
        self.initiatives.append(prev)
        self.initiatives.insert(0, last)

    def respondTo_inits(self, channel, user, _):
        """List inits, starting with the currently active character, in
        order"""
        # the "current" initiative is always at the end of the list
        current = self.initiatives[-1]
        inits = ['%s/%s' % (current[1], current[0])]
        for init in self.initiatives[:-1]:
            if init[1] is None:
                name = 'NEW ROUND'
            else:
                name = init[1]
            inits.append('%s/%s' % (name, init[0]))
        self.msg(channel, ', '.join(inits))

    def respondTo_combat(self, channel, user, _):
        """Start combat by resetting initiatives"""
        self.initiatives = [(9999, None)]
        self.msg(channel, '** Beginning combat **')

    def respondTo_party(self, channel, user, _):
        if len(self.party.bodies) == 0:
            self.msg(channel, '%s, nobody is in the party.' % (user,))
            return
        for char in self.party.bodies:
            self.msg(channel, '%(name)s: %(classes)s' % char.summarize())

    def respondTo_iam(self, channel, user, charname):
        """Take control of a character by name."""
        try:
            player = self.club.findExact(user)
        except ValueError:
            player = encounter.Player(user)
            self.club.registerPlayer(player)
        char = self.encounter.find(charname, first=1)
        player.own(char)
        self.msg(channel, "%s now owns %s." % (player.getName(), 
                                               char.getName()))

    def respondTo_remove(self, channel, user, charname):
        """Remove a character from an encounter by name."""
        char = self.party.dismiss(charname)
        self.msg(channel, "%s is no longer in the party." % 
                 (char.getName(),))

    def respondTo_help(self, channel, user, _):
        """This drivel."""
        _commands = []
        commands = []
        for att in dir(self):
            member = getattr(self, att)
            if (att.startswith('respondTo_') 
                and callable(member)
                and att[10:].upper() != att[10:]):  # DICE and DEFAULT reserved.
                _commands.append('%s: %s' % (att[10:], member.__doc__))
        _d = {'commands': '\n    '.join(_commands), 
              'nick': self.nickname}

        response = '''Recognized commands:
    %(commands)s
Commands can be used one of three ways, by hailing me, by /msg or with ".":
    Biff: %(nick)s: hello
    %(nick)s: Biff, hello.
    /msg %(nick)s: hello
    Private message from %(nick)s: Biff, hello.
    Biff: .hello
    %(nick)s: Biff, hello.
I also understand dice aliases...
    Biff: I roll [1d20+1]
    %(nick)s: Biff, you rolled 1d20+1 = [17]
    Biff: I roll [smackdown 1d10+17]
    %(nick)s: Biff, you rolled smackdown 1d10+17 = [23]
    Biff: I use a few more attacks, [smackdown] [smackdown]
    %(nick)s: Biff, you rolled smackdown = [21]
    %(nick)s: Biff, you rolled smackdown = [26]
I also can sort any dice alias result.  Use {} instead of []...
    Biff: I roll {stats 3d6x7}
    %(nick)s: Biff, you rolled stats 3d6x7 = {2, 9, 11, 13, 14, 14, 17} (sorted)
I also understand "npc hijacking".
    (TBD .. this may grow more features)
    Biff: *grimlock1 ... [foo 1d20+2]
    %(nick)s: grimlock1, you rolled foo 1d20+2 = [11]
''' % _d
        for line in response.splitlines():
            self.msg(channel, line)

    # irc callbacks

    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        # TODO - change the player name list


class VellumTalkFactory(protocol.ClientFactory):
    """A factory for VellumTalks.

    A new protocol instance will be created each time we connect to the server.
    """

    # the class of the protocol to build when new connection is made
    protocol = VellumTalk 

    def __init__(self, channel):
        self.channel = channel

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()

testcommands = [
('MFen', 'VellumTalk', 'MFen', 'hello', r'Hello MFen\.'),
('MFen', 'VellumTalk', 'MFen', 'VellumTalk: hello', r'Hello MFen\.'),
('MFen', 'VellumTalk', 'MFen', 'VellumTalk: hello there', r'Hello MFen\.'),
('MFen', 'VellumTalk', 'MFen', '.hello', r'Hello MFen\.'),
('MFen', '#vellum', '#vellum', 'hello', None),
('MFen', '#vellum', '#vellum', 'VellumTalk: hello', r'Hello MFen\.'),
('MFen', '#vellum', '#vellum', '.hello', r'Hello MFen\.'),
('MFen', 'VellumTalk', 'MFen', 'combat', r'\*\* Beginning combat \*\*'),
('MFen', '#vellum', '#vellum', '[init 20]', 
        r'MFen, you rolled: init 20 = \[20\]'),
('MFen', 'VellumTalk', 'MFen', 'n', r'\+\+ New round \+\+'),
            
('MFen', 'VellumTalk', 'MFen', 'n', 
        r'MFen \(init 20\) is ready to act \. \. \.'),
('MFen', 'VellumTalk', 'MFen', 'p', r'\+\+ New round \+\+'),
('MFen', 'VellumTalk', 'MFen', 'p', 
        r'MFen \(init 20\) is ready to act \. \. \.'),
('MFen', 'VellumTalk', 'MFen', 'inits', 
        r'MFen/20, NEW ROUND/9999'),
('MFen', 'VellumTalk', 'MFen', 'help', r'\s+hello: Greet\.'),
]
testdice = [
('MFen', '#vellum', '#vellum', 'I smackdown with [1d20+2]', 
        r'MFen, you rolled: 1d20\+2 = \[\S+\]'),
('MFen', '#vellum', '#vellum', 'I [smackdown 100]', 
        'MFen, you rolled: smackdown 100 = \[100\]'),
# the next 2 test the same thing.. that both inline expressions
# will get evaluated
('MFen', '#vellum', '#vellum', 'I [smackdown] [1]', 
 r'MFen, you rolled: 1 = \[1\]'),
('MFen', '#vellum', '#vellum', 'I [smackdown] [1]', 
 r'MFen, you rolled: smackdown = \[100\]'),

('MFen', 'VellumTalk', 'MFen', 'I [smackdown]', 
 r'MFen, you rolled: smackdown = \[100\]'),

# the next test is lame, but it'll have to do
('MFen', 'VellumTalk', 'MFen', '{100x2}',
        r'MFen, you rolled: 100x2 = {100, 100} \(sorted\)'),
]
testhijack = [
('MFen', 'VellumTalk', 'MFen', '*grimlock1 does a [smackdown 1000]', 
        'grimlock1, you rolled: smackdown 1000 = \[1000\]'),
('MFen', '#vellum', '#vellum', '*grimlock1 does a [bitchslap 1000]', 
        'grimlock1, you rolled: bitchslap 1000 = \[1000\]'),
('MFen', 'VellumTalk', 'MFen', '*grimlock1 does a [smackdown]', 
        'grimlock1, you rolled: smackdown = \[1000\]'),
('MFen', 'VellumTalk', 'MFen', 'I do a [smackdown]', 
        'MFen, you rolled: smackdown = \[100\]'),
]

# TODO - move d20-specific tests, e.g. init and other alias hooks?

def test():
    from twisted.words.test.test_irc import StringIOWithoutClosing
    f = StringIOWithoutClosing()
    transport = protocol.FileWrapper(f)
    vt = VellumTalk()
    vt.performLogin = 0
    vt.responding = 1
    vt.makeConnection(transport)
    pos = ([0],)

    def check(nick, channel, target, expected):
        _pos = pos[0] # ugh, python
        f.seek(_pos.pop(0))
        actual = f.read().strip()
        _pos.append(f.tell())
        if expected is None:
            if actual == '':
                pass
            else:
                print
                print ' '*10 + ' '*len(target) + expected
                print actual
                return
        else:
            for _line in actual.splitlines():
                pattern = 'PRIVMSG %s :%s' % (re.escape(target), expected)
                if re.match(pattern, _line):
                    break
            else:
                print
                print ' '*10 + ' '*len(target) + expected
                print actual
                return
        print '+++'


    for nick, channel, target, sent, received in testcommands:
        vt.privmsg(nick, channel, sent)
        check(nick, channel, target, received)
    for nick, channel, target, sent, received in testdice:
        vt.privmsg(nick, channel, sent)
        check(nick, channel, target, received)
        vt.action(nick, channel, sent)
        check(nick, channel, target, received)
    for nick, channel, target, sent, received in testhijack:
        vt.privmsg(nick, channel, sent)
        check(nick, channel, target, received)

