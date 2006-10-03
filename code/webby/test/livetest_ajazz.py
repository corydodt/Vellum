from twisted.internet import defer

from nevow import athena
from nevow.livetrial import testcase

from webby import ajazz
from webby.minchat import IChatConversations, NullConversation

class MockAccountManager:
    def doConnection(self, host, username, password, channels):
        return defer.succeed(None)

class TestIRCContainer(testcase.TestCase):
    jsClass = u'WebbyVellum.Tests.TestIRCContainer'
    def generateConversation(self, id):
        """
        Hook up a new (fake) conversation so tests can play with the tab.
        """
        convwin = IChatConversations(self.irc)
        nullconv = NullConversation(convwin, id)
        return convwin.showConversation(nullconv, id)
    athena.expose(generateConversation)

    def newContainer(self, ):
        """
        Return a new IRC Container with mock conversations for the ids given
        """
        # XXX warning - livetrial does not provide test isolation!
        # setting instance variables can bite you in the ass.  If this
        # method is called first from every test, life is fine, but if
        # generateConversation is called without calling this first,
        # behavior is UNDEFINED.
        self.irc = ajazz.IRCContainer(MockAccountManager())
        self.irc.setFragmentParent(self)
        return self.irc
    athena.expose(newContainer)

