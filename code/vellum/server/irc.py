"""
Vellum's face.  The bot that answers actions in the channel.
"""
# system imports
import time, sys
import re
import traceback
import glob

# twisted imports
from twisted.protocols import irc
from twisted.internet import reactor, protocol, task
from twisted.python import log


from vellum.server import dice, encounter
from vellum.server.fs import fs



class VellumTalk(irc.IRCClient):
    """A logging IRC bot."""

    def __init__(self, *args, **kwargs):
        self.encounters = []
        self.party = encounter.Encounter()
        self.roller = dice.Roller()
        self.wtf = 0  # number of times a "wtf" has occurred recently.
        # reset wtf's every 30 seconds 
        self.resetter = task.LoopingCall(self._resetWtfCount).start(30.0)

        self.responding = 0 # don't start responding until i'm in a channel
        self.club = encounter.Club()
        self._loadParty()
        # irc.IRCClient.__init__(self, *args, **kwargs)
    
    nickname = "VellumTalk"
    
    def connectionMade(self):
        irc.IRCClient.connectionMade(self)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        # TODO - this might be a good place to save


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

    def _resetWtfCount(self):
        self.wtf = 0

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

    def respondTo_DICE(self, channel, user, exp):
        """{d1ce} expressions -- see dice.py for user syntax"""
        if exp[0] == '[':
            sorted = 1
        else:
            sorted = 0
        exp = exp.strip('{}[]')
        try:
            roll = self.roller.roll(exp)
            if sorted:
                roll.sort()
                roll = map(str, roll)
                _roll = '[%s]' % (', '.join(roll),)
                if len(roll) > 1:
                    _roll = _roll + ' (sorted)'
            else:
                roll = map(str, roll)
                _roll = '{%s}' % (', '.join(roll),)
            response = '%s, you rolled: %s = %s' % (user, exp, _roll)
            self.msg(channel, response)
        except RuntimeError, e:
            pass

    def respondTo_hello(self, channel, user, _):
        """Greet."""
        self.msg(channel, 'Hello %s.' % (user,))

    def _loadParty(self):
        """Load characters in the party/ dir"""
        for filename in glob.glob(fs.party('*.yml')):
            char = encounter.Character(filename=fs.party(filename))
            self.party.addCharacter(char)

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
