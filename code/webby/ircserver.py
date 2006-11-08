from zope.interface import implements

from twisted.words import service
from twisted.cred import checkers, portal, credentials

from webby import theGlobal, data

theRealm = service.InMemoryWordsRealm('vellumIRCserver')
theRealm.createGroupOnRequest = True

class AxiomNickChecker(object):
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = credentials.IUsernamePassword,

    def requestAvatarId(self, credentials):
        store = theGlobal['dataService'].store

        username = unicode(credentials.username)
        password = unicode(credentials.password)

        u = store.findFirst(data.User, data.User.nick==username)

        if u is not None and u.password == password:
            if u.enabled: # user must have clicked the emailed link before login
                return credentials.username # 8-bit string username, not unicode

        return error.LoginFailed()


checker = AxiomNickChecker()

thePortal = portal.Portal(theRealm, [checker])

theIRCFactory = service.IRCFactory(theRealm, thePortal)
