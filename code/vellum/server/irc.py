"""
Vellum's face.  The bot that answers actions in the channel.
"""
# system imports
import time, sys
import re
import traceback
import glob
import errno
import atexit
try:
    from cPickle import dump, load
except ImportError:
    from pickle import dump, load

# twisted imports
from twisted.protocols import irc
from twisted.internet import reactor, protocol, task
from twisted.python import log


from vellum.server import encounter, alias
from vellum.server.fs import fs

def saveAliases():
    print 'saving aliases'
    dump(alias.aliases, file(fs.aliases('aliases.pkl'), 'wb'))

def loadAliases():
    try:
        alias.aliases = load(file(fs.aliases('aliases.pkl'), 'rb'))
        print 'loaded aliases'
    except IOError, e:
        # if the file just doesn't exist, assume we have to create it.
        if e.errno == errno.ENOENT:
            print 'new aliases.pkl'
        else:
            raise


atexit.register(saveAliases)


class VellumTalk(irc.IRCClient):
    """A logging IRC bot."""
    
    nickname = "VellumTalk"

    def __init__(self, *args, **kwargs):
        loadAliases() # FIXME! - if we're going to overwrite aliases at 
                      # shutdown, we HAVE to load them at startup.
                      # if VellumTalk never initializes, aliases.pkl
                      # gets written EMPTY
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
        print user, channel, msg
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
        hail = self.nickname.lower() + ':'
        if msg.lower().startswith(hail):
            command = msg[len(hail):]
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
        print user, channel, msg
        if not self.responding:
            return
        if channel == self.nickname:
            channel = user

        # only dice are handled in actions
        self._handleDice(channel, user, msg)

    def dispatchCommand(self, channel, user, command):
        """Choose a method based on the command word, and pass args if any"""
        command_word = 'DEFAULT'
        args = None
        if command:
            _splits = command.split(None, 1)
            command_word = _splits.pop(0)
            if len(_splits) > 0:
                args = _splits[0]
        if re.match(r'\[.+?\]|{.+?}', command_word):
            return self._handleDice(channel, user, command)
        m = getattr(self, 'respondTo_%s' % (command_word,), 
                    self.respondTo_DEFAULT)
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
        self.msg(channel, '%s (init %s)' % (next[1], next[0],))
        self.initiatives.append(next)

    def respondTo_p(self, channel, user, _):
        """Previous initiative"""
        prev = self.initiatives.pop(-1)
        _init = self.initiatives[-1]
        self.msg(channel, '%s (init %s)' % (_init[1], _init[0],))
        self.initiatives.insert(0, prev)

    def respondTo_combat(self, channel, user, _):
        """Start combat by resetting initiatives"""
        self.initiatives = [(9999, '++ New round ++')]
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
        self.msg(channel, user + ', help is on the way. (TBD)')

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