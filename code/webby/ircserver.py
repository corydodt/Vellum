from time import time

from zope.interface import implements

from twisted.internet import defer
from twisted.words.service import InMemoryWordsRealm, IRCFactory, IRCUser, \
                                  User, Group
from twisted.words import iwords
from twisted.words.protocols import irc
from twisted.cred import checkers, portal, credentials, error

from webby import theGlobal, data, util

from axiom import item, attributes as A

class VellumIRCUser(User):
    def sendNotice(self, recipient, message):
        self.lastMessage = time()
        return recipient.receiveNotice(self.mind, recipient, message)


class VellumIRCGroup(Group):
    def receiveNotice(self, sender, recipient, message):
        # raped n pasted from irc.py Group.receive()
        assert recipient is self
        receives = []
        for p in self.users.itervalues():
            if p is not sender:
                d = defer.maybeDeferred(p.receiveNotice, sender, self, message)
                d.addErrback(self._ebUserCall, p=p)
                receives.append(d)
        defer.DeferredList(receives).addCallback(self._cbUserCall)
        return defer.succeed(None)


class VellumWordsRealm(InMemoryWordsRealm):
    def userFactory(self, name):
        return VellumIRCUser(name)

    def groupFactory(self, name):
        return VellumIRCGroup(name)


theRealm = VellumWordsRealm('vellumIRCserver')
theRealm.createGroupOnRequest = True


class VellumIRCServerProtocol(IRCUser):
    def receiveNotice(self, sender, recipient, message):
        # raped n pasted from irc.py receive()
        if iwords.IGroup.providedBy(recipient):
            recipientName = '#' + recipient.name
        else:
            recipientName = recipient.name

        text = message.get('text', '<an unrepresentable message>')
        for L in text.splitlines():
            self.notice(
                '%s!%s@%s' % (sender.name, sender.name, self.hostname),
                recipientName,
                L)

    def irc_NOTICE(self, prefix, params):
        """Process a NOTICE.

        Parameters: <msgtarget> <text to be sent>

        RAPED AND PASTED from IRCUser.irc_PRIVMSG
        """
        try:
            targetName = params[0].decode(self.encoding)
        except UnicodeDecodeError:
            self.sendMessage(
                irc.ERR_NOSUCHNICK, targetName,
                ":No such nick/channel (could not decode your unicode!)")
            return

        messageText = params[-1]
        if targetName.startswith('#'):
            target = self.realm.lookupGroup(targetName[1:])
        else:
            target = self.realm.lookupUser(targetName).addCallback(lambda user: user.mind)

        def cbTarget(targ):
            if targ is not None:
                return self.avatar.sendNotice(targ, {"text": messageText})

        def ebTarget(err):
            self.sendMessage(
                irc.ERR_NOSUCHNICK, targetName,
                ":No such nick/channel.")

        target.addCallbacks(cbTarget, ebTarget)


class VellumIRCFactory(IRCFactory):
    protocol = VellumIRCServerProtocol


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

class IRCService(item.Item, util.AxiomTCPServerMixin):
    factory = VellumIRCFactory(theRealm, thePortal)
    schemaVersion = 1
    portNumber = A.integer()

    port = A.inmemory()
    parent = A.inmemory()
    running = A.inmemory()

