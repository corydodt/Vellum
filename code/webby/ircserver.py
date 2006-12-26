"""
Implement the SERVER-SIDE IRC protocol.
"""
from time import time

from zope.interface import implements

from twisted.internet import defer
from twisted.python import log, failure
from twisted.words.service import InMemoryWordsRealm, IRCFactory, IRCUser, \
                                  User, Group
from twisted.words import iwords
from twisted.words.protocols import irc
from twisted.cred import checkers, portal, credentials, error
from twisted.test import proto_helpers

from webby import theGlobal, data, util

from axiom import item, attributes as A

from epsilon.extime import Time

VELLUMTALK = u"VellumTalk!vellumtalk@vellum.berlios.de"
VTNICK = VELLUMTALK.split('!', 1)[0]

class VellumIRCUser(User):
    def sendNotice(self, recipient, message):
        self.lastMessage = time()
        return recipient.receiveNotice(self.mind, recipient, message)


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

    def getTarget(self, params):
        """
        Parse params for the target and messageText, and return the
        actual target
        """
        try:
            targetName = params[0].decode(self.encoding)
        except UnicodeDecodeError, e:
            self.sendMessage(
                irc.ERR_NOSUCHNICK, targetName,
                ":No such nick/channel (could not decode your unicode!)")
            return failure.Failure(e)

        messageText = params[-1]

        if targetName.startswith('#'):
            d = self.realm.lookupGroup(targetName[1:])
        else:
            d = self.realm.lookupUser(targetName).addCallback(lambda u: u.mind)

        def cbTarget(targetobj):
            return targetobj, messageText

        def ebTarget(err):
            self.sendMessage(
                irc.ERR_NOSUCHNICK, targetName,
                ":No such nick/channel.")
            return err

        d.addCallbacks(cbTarget, ebTarget)

        return d

    def irc_NOTICE(self, prefix, params):
        """Process a NOTICE.

        Parameters: <msgtarget> <text to be sent>
        """
        return self.getTarget(params).addCallback(self.irctarget_NOTICE, prefix)

    def irctarget_NOTICE(self, (target, messageText), prefix):
        if target is not None:
            return self.avatar.sendNotice(target, {"text": messageText})

    def irc_AWAY(self, prefix, params):
        """Ignore away messages sent by wayward clients, for now."""

    def irc_BACKGROUND(self, prefix, params):
        """
        /BACKGROUND #channel md5key

        Set the channel map's background. This will also resize the map.
        """
        return self.getTarget(params).addCallback(self.irctarget_BACKGROUND, prefix)

    def irctarget_BACKGROUND(self, (group, messageText), prefix, ):
        md5key = messageText
        messageText = u'BACKGROUND #%s %s' % (group.name, messageText,)

        assert iwords.IGroup.providedBy(group), "Target must be a group"
        
        # TODO - permissions.  Am I allowed to do this in this channel?

        d = theRealm.lookupUser(VTNICK.lower())

        def cbUser(client):
            # persist!
            db = theGlobal['database']
            FM = data.FileMeta
            filemeta = db.findFirst(FM, FM.md5 == unicode(md5key))
            group.channelItem.setBackground(filemeta)

            # tell others.
            message = {'text': messageText}
            client.sendNotice(group, message)

        d.addCallback(cbUser)

    def irc_OBSCUREALL(self, prefix, params):
        """
        /OBSCUREALL #channel

        Make the map completely covered by obscurement.
        """
        return self.getTarget(params).addCallback(self.irctarget_OBSCUREALL, prefix)

    def irctarget_OBSCUREALL(self, (group, messageText), prefix, ):
        messageText = u'OBSCUREALL #%s' % (group.name, )

        assert iwords.IGroup.providedBy(group), "Target must be a group"
        
        # TODO - permissions.  Am I allowed to do this in this channel?

        d = theRealm.lookupUser(VTNICK.lower())

        def cbUser(client):
            # persist!
            group.channelItem.obscureAll()

            # tell others.
            message = {'text': messageText}
            client.sendNotice(group, message)

        d.addCallback(cbUser)

    def irc_REVEALALL(self, prefix, params):
        """
        /REVEALALL #channel

        Make the map completely covered by obscurement.
        """
        return self.getTarget(params).addCallback(self.irctarget_REVEALALL, prefix)

    def irctarget_REVEALALL(self, (group, messageText), prefix, ):
        messageText = u'REVEALALL #%s' % (group.name, )

        assert iwords.IGroup.providedBy(group), "Target must be a group"
        
        # TODO - permissions.  Am I allowed to do this in this channel?

        d = theRealm.lookupUser(VTNICK.lower())

        def cbUser(client):
            # persist!
            group.channelItem.revealAll()

            # tell others.
            message = {'text': messageText}
            client.sendNotice(group, message)

        d.addCallback(cbUser)

    def _sendTopic(self, group):
        """
        Look up the topic in the database
        """
        topic = group.channelItem.topic
        author = group.channelItem.topicAuthor or "<noone>"
        date = group.channelItem.topicTime
        if date is None:
            date = 0
        else:
            date = date.asPOSIXTimestamp()
        self.topic(self.name, '#' + group.name, topic)
        self.topicAuthor(self.name, '#' + group.name, author, date)

    def irc_MAPDIGEST(self, prefix, params):
        """
        /MAPDIGEST #channel
            Request the whole map state upon entering a channel.
        """
        return self.getTarget(params).addCallback(self.irctarget_MAPDIGEST, prefix)

    def irctarget_MAPDIGEST(self, (group, messageText), prefix):
        """
        Request a digest from the channelItem.
        We will then send:
            MAPDIGEST #channel
            ... all of the digested commands ...
            ENDDIGEST #channel

        The client is expected to queue any other commands it receives
        during a digest session, and process them only after it has
        received ENDDIGEST.
        """
        channel = messageText
        assert iwords.IGroup.providedBy(group), "Target must be a group"
        
        d = theRealm.lookupUser(VTNICK.lower())

        def cbUser(client):
            text = u'MAPDIGEST %s' % (channel,)

            message = {'text': text}
            client.sendNotice(self, message)
            digest = group.channelItem.getDigestedForm()
            for command in digest:
                client.sendNotice(self, {'text':command})
            client.sendNotice(self, {'text':'ENDDIGEST %s' % (channel,)})

        d.addCallback(cbUser)

    """
    /NEWMAP #channel
        clean the channel map of all tokens, drawings, obscurement and
        background

    /MAPSCALE #channel distance
        Set the map's scale so that 100px==distance.  Resize tokens
        appropriately.

    /ADDTOKEN #channel protoid (TBD...)
        Create a new token from the prototype, ...

    /DELTOKEN #channel tokenid
        Remove the token from the map.

    /MOVETOKEN #channel tokenid destx desty
        Move the token to a new location.

    /OBSCUREMENT #channel (TBD...)
        Update the map obscurement ...

    /ADDDRAWING #channel (TBD...)
        Add an SVG drawing to the map ...

    /DELDRAWING #channel (TBD...)
        Remove the drawing from the map

    /MOVEDRAWING #channel (TBD...)
        Move the drawing on the map

    (TBD ... time commands)
    """


class VellumIRCGroup(Group):
    def __init__(self, *a, **kw):
        Group.__init__(self, *a, **kw)
        db = theGlobal['database']
        Ch = data.Channel
        self.channelItem = db.findOrCreate(Ch, name=u'#%s' % (self.name,))

        d = theRealm.lookupUser(VTNICK)

        def cbLookup(user):
            self.users[VTNICK] = user.mind

        d.addCallback(cbLookup)

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

    def setMetadata(self, meta):
        """
        Set the topic in the database
        """
        self.channelItem.topic = unicode(meta['topic'])
        self.channelItem.topicAuthor = unicode(meta['topic_author'])
        self.channelItem.topicTime = Time.fromPOSIXTimestamp(meta['topic_date'])
        sets = []
        for p in self.users.itervalues():
            d = defer.maybeDeferred(p.groupMetaUpdate, self, meta)
            d.addErrback(self._ebUserCall, p=p)
            sets.append(d)
        defer.DeferredList(sets).addCallback(self._cbUserCall)
        return defer.succeed(None)


class VellumWordsRealm(InMemoryWordsRealm):
    def userFactory(self, name):
        return VellumIRCUser(name)

    def groupFactory(self, name):
        return VellumIRCGroup(name)


theRealm = VellumWordsRealm('vellumIRCserver')
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


class DummyStringTransport(proto_helpers.StringTransport):
    def write(self, data):
        pass

    def writeSequence(self, data):
        pass

    def value(self):
        raise NotImplementedError()


class IRCService(item.Item, util.AxiomTCPServerMixin):
    @staticmethod
    def factory():
        f = IRCFactory(theRealm, thePortal)
        f.protocol = VellumIRCServerProtocol
        return f

    schemaVersion = 1
    portNumber = A.integer(doc="The port on which to run.")
    interface = A.text(
          doc="Dotted-decimal interface to run on, '' for all interfaces", 
          default=u'')

    port = A.inmemory()
    parent = A.inmemory()
    running = A.inmemory()

    def startService(self):
        super(IRCService, self).startService()
        # create VellumTalk, a default User
        d = theRealm.createUser(VTNICK)
        def _created(user):
            # set up vellumtalk's mind and misc. attributes
            user.mind = VellumIRCServerProtocol()
            user.mind.makeConnection(DummyStringTransport())
            user.mind.avatar = user
            user.mind.name = VTNICK
            # need a signOn for whois
            user.signOn = time()
            return user
        d.addCallback(_created)
        d.addCallback(lambda u: log.msg("Created user %r" % (u.name,)))

