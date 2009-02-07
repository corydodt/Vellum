from twisted.internet import defer

from nevow import athena
from nevow.livetrial import testcase

from webby import signup

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
    jsClass = u'Signup.Tests.TestSignup'
    def newSignup(self, ):
        """
        Return a new Signup widget
        """
        su = StubSignup('http://')
        su.setFragmentParent(self)
        return su

    athena.expose(newSignup)

