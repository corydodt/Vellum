from zope.interface import implements

from twisted.words import service
from twisted.cred import checkers, portal, credentials, error

from webby import theGlobal, data

theRealm = service.InMemoryWordsRealm('vellumIRCserver')
theRealm.createGroupOnRequest = True

class AxiomNickChecker(object):
    """
    Mostly cloned from webby.web.AxiomEmailChecker
    """
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = credentials.IUsernamePassword,

    def requestAvatarId(self, credentials):
        store = theGlobal['dataService'].store

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

theIRCFactory = service.IRCFactory(theRealm, thePortal)
