from twisted.internet import defer

from nevow import athena
from nevow.livetrial import testcase

from webby import ircweb, data, gmtools, iwebby
from webby.minchat import NullConversation
from webby.test.teststore import cleanStore, testUser

class MockMinAccountManager:
    def doConnection(self, host, username, password, channels):
        return defer.succeed(None)

    def disconnect(self, *a, **kw):
        """Just to make nit happy"""

class MockConversation:
    def sendText(self, message):
        pass

class TestChatEntry(testcase.TestCase):
    jsClass = u'WebbyVellum.Tests.TestChatEntry'
    def newChatEntry(self, ):
        """
        Return a new chat entry
        """
        chatentry = ircweb.ChatEntry(MockConversation())
        chatentry.setFragmentParent(self)
        return chatentry

    athena.expose(newChatEntry)


class TestIRCContainer(testcase.TestCase):
    jsClass = u'WebbyVellum.Tests.TestIRCContainer'
    def generateConversation(self, id):
        """
        Hook up a new (fake) conversation so tests can play with the tab.
        """
        convwin = iwebby.IChatConversations(self.irc)
        nullconv = NullConversation(convwin, id)
        return convwin.showConversation(nullconv, id)

    athena.expose(generateConversation)

    def newContainer(self, ):
        """
        Return a new IRC Container with mock conversations for the ids given
        """
        user = testUser(cleanStore())
        # XXX warning - livetrial does not provide test isolation!
        # setting instance variables can bite you in the ass.  If this
        # method is called first from every test, life is fine, but if
        # generateConversation is called without calling this first,
        # behavior is UNDEFINED.
        self.irc = ircweb.IRCContainer(MockMinAccountManager(), user)
        self.irc.setFragmentParent(self)

        return self.irc

    athena.expose(newContainer)


class TestAccountManager(testcase.TestCase):
    jsClass = u'WebbyVellum.Tests.TestAccountManager'
    def newAccountManager(self, nick=None, autoHide=None):
        """
        Return a new Account Manager
        """
        user = testUser(cleanStore())
        if nick is not None:
            user.nick = nick
        am = ircweb.AccountManager(MockMinAccountManager(), None, user)
        am.setFragmentParent(self)
        return am

    athena.expose(newAccountManager)


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

class TestFileChooser(testcase.TestCase):
    jsClass = u'WebbyVellum.Tests.TestFileChooser'
    def newFileChooser(self, labels=None):
        """
        Return a new Signup widget
        @param labels: create ChooserIcons with the given labels as well
        """
        # if labels was given, create some test files.  FileChooser
        # will make ChooserIcons out of these during rendering
        self.store = cleanStore()
        self.user = testUser(self.store)
        if labels is not None:
            for label in labels:
                fileitem = data.FileMeta(store=self.store, user=self.user,
                        filename=label, mimeType=u'text/plain')

        self.fc = gmtools.FileChooser(self.user)
        self.fc.setFragmentParent(self)

        return self.fc

    athena.expose(newFileChooser)

    def addNewIcon(self, label):
        fileitem = data.FileMeta(store=self.store, user=self.user,
                filename=label, mimeType=u'text/plain')
        return self.fc.user.fileAdded(fileitem)

    athena.expose(addNewIcon)

class TestNameSelect(testcase.TestCase):
    jsClass = u'WebbyVellum.Tests.TestNameSelect'
    def newNameSelect(self, ):
        """
        Return a new NameSelect
        """
        ns = ircweb.NameSelect()
        ns.setFragmentParent(self)
        return ns

    athena.expose(newNameSelect)


class TestConversationEnclosure(testcase.TestCase):
    jsClass = u'WebbyVellum.Tests.TestConversationEnclosure'
    def newConversationEnclosure(self, ):
        """Return a new ConversationEnclosure"""
        ce = ircweb.ConversationEnclosure(u"#foo",
                    userClass="gameTab", 
                    decorated=False)
        ce.setFragmentParent(self)
        return ce

    athena.expose(newConversationEnclosure)
