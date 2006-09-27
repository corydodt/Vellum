from twisted.internet import defer

from nevow import athena
from nevow.livetrial import testcase

from webby import ajazz

class MockAccountManager:
    def doConnection(self, host, username, password, channels):
        return defer.succeed(None)

class TestIRCContainer(testcase.TestCase):
    jsClass = u'WebbyVellum.Tests.TestIRCContainer'
    def newContainer(self, ):
        """Return a new IRC Container"""
        w = ajazz.IRCContainer(MockAccountManager())
        w.setFragmentParent(self)
        return w
    athena.expose(newContainer)

