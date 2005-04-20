"""
Vellum's face.  The bot that answers actions in the channel.
"""
# system imports
import time, sys
import re


# twisted imports
from twisted.protocols import irc
from twisted.internet import reactor, protocol, task
from twisted.python import log

import yaml

from vellum.server import dice


class MessageLogger:
    """
    An independant logger class (because separation of application
    and protocol logic is a good thing).
    """
    def __init__(self, file):
        self.file = file

    def log(self, message):
        """Write a message to the file."""
        timestamp = time.strftime("[%H:%M:%S]", time.localtime(time.time()))
        self.file.write('%s %s\n' % (timestamp, message))
        self.file.flush()

    def close(self):
        self.file.close()


class LogBot(irc.IRCClient):
    """A logging IRC bot."""

    def __init__(self, *args, **kwargs):
        self.roller = dice.Roller()
        self.wtf = 0  # number of times a "wtf" has occurred recently.
        # reset wtf's every 30 seconds 
        self.resetter = task.LoopingCall(self._resetWtfCount).start(30.0)

        self.responding = 0 # don't start responding until i'm in a channel
        # irc.IRCClient.__init__(self, *args, **kwargs)
    
    nickname = "VellumTalk"
    
    def connectionMade(self):
        irc.IRCClient.connectionMade(self)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)


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
        dice_expressions = re.findall('{.+?}', msg)
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
        m = getattr(self, 'respondTo_%s' % (command_word,), 
                    self.respondTo_DEFAULT)
        m(channel, user, args)

    def _resetWtfCount(self):
        self.wtf = 0

    def respondTo_DEFAULT(self, channel, user, args):
        # we don't want to get caught looping, so respond up to 3 times
        # with wtf, then wait for the counter to reset
        if self.wtf < 3:
            self.msg(channel, "wtf?")
            self.wtf = self.wtf + 1

    def respondTo_DICE(self, channel, user, exp):
        """{d1ce} expressions -- see dice.py for user syntax"""
        exp = exp.strip('{}')
        try:
            roll = self.roller.roll(exp)
            response = '%s, you rolled: %s = %s' % (user, exp, roll)
            self.msg(channel, response)
        except RuntimeError, e:
            pass

    def respondTo_hello(self, channel, user, _):
        """Greet."""
        self.msg(channel, 'Hello %s.' % (user,))

    def respondTo_load(self, channel, user, filename):
        """Load a character from a yml file"""
        char = yaml.loadFile(filename).next()
        self.msg(channel, 
                 user + ', I loaded %(name)s, a %(classes)s' % char)

    def respondTo_help(self, channel, user, _):
        self.msg(channel, user + ', help is on the way. (TBD)')

    # irc callbacks

    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]


class VellumTalk(protocol.ClientFactory):
    """A factory for LogBots.

    A new protocol instance will be created each time we connect to the server.
    """

    # the class of the protocol to build when new connection is made
    protocol = LogBot

    def __init__(self, channel):
        self.channel = channel

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()
