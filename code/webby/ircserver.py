from twisted.words import service
from twisted.cred import checkers, portal

theRealm = service.InMemoryWordsRealm('vellumIRCserver')
theRealm.createGroupOnRequest = True

checker = checkers.InMemoryUsernamePasswordDatabaseDontUse()
checker.addUser('MFen', 'ninjas')
checker.addUser('bot', 'ninjas')

thePortal = portal.Portal(theRealm, [checker])

theIRCFactory = service.IRCFactory(theRealm, thePortal)
