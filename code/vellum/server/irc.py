"""
Vellum's face.  The bot that answers actions in the channel.
"""
import re

# twisted imports
from twisted.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

# system imports
import time, sys

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

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        private = 0
        user = user.split('!', 1)[0]
        
        # Check to see if they're sending me a private message
        if channel == self.nickname:
            private = 1
            msg = "I should know how to respond to you by private message :("
            self.msg(user, msg)
            return

        dice_expressions = re.findall('{.+?}', msg)
        for exp in dice_expressions:
            self.respondTo_dice(channel, user, exp[1:-1], private)


    def respondTo_dice(self, channel, user, exp, private=0):
        try:
            roll = self.roller.roll(exp)
            response = '%s, you rolled: %s = %s' % (user, exp, roll)
            self.msg(channel, response)
        except RuntimeError, e:
            pass
        

    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        user = user.split('!', 1)[0]

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
