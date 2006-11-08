from twisted.internet import defer

from axiom import store

from nevow import athena
from nevow.livetrial import testcase

from webby import ircweb, signup, data, theGlobal
from webby.minchat import IChatConversations, NullConversation

class MockAccountManager:
    def doConnection(self, host, username, password, channels):
        return defer.succeed(None)

# define our in-memory test store
testStore = store.Store()
testUser = data.User(store=testStore, 
        email=u'woot@woot.com', nick=u'woot', password=u'ninjas')
theGlobal['dataService'] = data.DataService(testStore)


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
        self.irc = ircweb.IRCContainer(MockAccountManager(), testUser)
        self.irc.setFragmentParent(self)

        # reset the default nick between each test
        testUser.nick = u'woot'

        return self.irc

    athena.expose(newContainer)

class TestTopicBar(testcase.TestCase):
    jsClass = u'WebbyVellum.Tests.TestTopicBar'
    def newTopicBar(self, ):
        """
        Return a new Topic Bar
        """
        tb = ircweb.TopicBar()
        tb.setFragmentParent(self)
        return tb

    athena.expose(newTopicBar)

class StubSignup(signup.Signup):
    """Signup widget that doesn't really send email."""
    def processSignup(self, email, password):
        """
        Make it succeed or fail by passing an email address with or without
        an @ sign.
        """
        if '@' in email:
            d = defer.succeed(None)
        else:
            1/0
        return d

    athena.expose(processSignup)

class TestSignup(testcase.TestCase):
    jsClass = u'WebbyVellum.Tests.TestSignup'
    def newSignup(self, ):
        """
        Return a new Signup widget
        """
        su = StubSignup('http://')
        su.setFragmentParent(self)
        return su

    athena.expose(newSignup)
