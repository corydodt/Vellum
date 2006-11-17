from zope.interface import implements

from twisted.words.service import InMemoryWordsRealm, IRCFactory
from twisted.cred import checkers, portal, credentials, error
from twisted.application import internet
from twisted.application.service import IService
from twisted.internet import reactor

from axiom import item, attributes as A

from webby import theGlobal, data

theRealm = InMemoryWordsRealm('vellumIRCserver')
theRealm.createGroupOnRequest = True

class AxiomNickChecker(object):
    """
    Mostly cloned from webby.web.AxiomEmailChecker
    """
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = credentials.IUsernamePassword,

    def requestAvatarId(self, credentials):
        store = theGlobal['database']

        username = unicode(credentials.username)
        password = unicode(credentials.password)

        u = store.findFirst(data.User, data.User.nick==username)

        # Note: If the account has not been confirmed from the email
        # address, u.password will be None.
        if u is not None and u.password == password:
            # clear unconfirmedPassword here.  This is needed if either of the
            # following occurs:
            # a) user visits the forgot password page but subsequently
            # remembers the original password
            # b) malicious user visits the forgot password page but can't
            # confirm the new password, and the real user logs in at some
            # point.
            u.unconfirmedPassword = None
            return credentials.username

        raise error.UnauthorizedLogin()

checker = AxiomNickChecker()

thePortal = portal.Portal(theRealm, [checker])

theIRCFactory = IRCFactory(theRealm, thePortal)

class IRCService(item.Item, internet.TCPServer, item.InstallableMixin):
    schemaVersion = 1
    portNumber = A.integer()

    port = A.inmemory()
    parent = A.inmemory()
    running = A.inmemory()

    def privilegedStartService(self):
        pass

    def startService(self):
        self.port = reactor.listenTCP(self.portNumber, theIRCFactory)

    def installOn(self, other):
        super(IRCService, self).installOn(other)
        other.powerUp(self, IService)
        if self.parent is None:
            self.setServiceParent(other)

