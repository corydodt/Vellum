"""
Implement the CLIENT-SIDE GUI glue of the IRC functionality.  Objects in here
are components used by the web GUI, and glue the low-level client-side IRC
protocol in proto.py to the raw GUI in ircweb.py.

Most likely this stuff could all be moved into existing classes in ircweb.py.
"""

from twisted.words.im import basechat, baseaccount, ircsupport
from twisted.internet import defer, protocol, reactor
from twisted.python import components

from zope.interface import implements

from webby.proto import WebbyAccount # Using custom account, so as to use a custom protocol
from webby import iwebby

ACCOUNTS = {}

PROTOS = {}

IRCPORT = 6667

class MinAccountManager(baseaccount.AccountManager):
    """
    This class is a minimal implementation of the Acccount Manager.
    """

    def __init__(self, chatui):
        baseaccount.AccountManager.__init__(self)
        self.chatui = chatui

    def doConnection(self, host, username, password, channels):
        key = (username, host)
        if key in ACCOUNTS:
            self.disconnectAsNeeded(ACCOUNTS[key])

        # If we make it so we use our own subclass of IRCAccount here, instead
        # of the stock one, and overload _startLogin, we can do protocol
        # actions at the protocol.  Ooooh LA!

        acct = WebbyAccount('%s@%s' % key,
                                     1, username, password, 
                                     host, IRCPORT, channels) # custom account
        ACCOUNTS[key] = acct
        d = acct.logOn(self.chatui)

        def _addProto(proto, acct, key):
            PROTOS[key] = proto
            return acct

        d.addCallback(_addProto, acct, key)

        return d

    def disconnectAsNeeded(self, account):
        if account.isOnline():
            self.disconnect(account)
        
    def disconnect(self, account):
        key = (account.username, account.host)
        PROTOS[key].transport.loseConnection()
        del PROTOS[key]
        del ACCOUNTS[key]


class UnformattableMessage(Exception):
    pass


IChatFormatter = iwebby.IChatFormatter


class ChatFormatter(object):
    implements(IChatFormatter)

    def format(self, text, sender=None, target=None, metadata=None):
        if metadata is None: metadata = {}

        if not sender and not target:
            raise UnformattableMessage("sender=%r,target=%r" % (sender, target))

        name = sender or target

        # TODO - when target is given instead of sender, use different
        # formatting (e.g. >Nick< )

        if metadata.get("style", None) == "emote":
            t = '* %s %s' % (name, text)
        elif metadata.get('dontAutoRespond', False):
            t = "-%s- %s" % (name, text)
        else:
            t = "<%s> %s" % (name, text)

        return t


class NullConversation(components.Componentized):
    """This conversation is a placeholder without an actual interface to IRC.
    It should be used for things like server tabs in the UI.
    """
    def __init__(self, widget, name):
        components.Componentized.__init__(self)
 
    def sendText(self, text, metadata=None):
        if metadata is None:
            style = ''
        else:
            style = u'(%s) ' % (metadata.get('style', ''),)
        text = unicode(style + text)
        return iwebby.ITextArea(self).printClean(
                '** Not in a channel or conversation: %s' % (text,))


class ReceivedNoticeParser(object):
    def __init__(self, groupConversation):
        self.groupConversation = groupConversation
        ## self.backlog = []
        ## self.receivingDigest = False

    def parse(self, command, channel, args):
        try:
            meth = getattr(self, 'command_%s' % (command.upper(),))
            ## if self.receivingDigest:
                ## # queue commands that aren't received as part of the digest
                ## # TODO - differentiate simultaneous MAPDIGEST requests
                ## d = defer.Deferred()
                ## self.backlog.append((d, meth, command, args))
                ## return d
            ## else:
            return meth(command, args)
        except AttributeError, e:
            return
                
    def command_BACKGROUND(self, command, md5key):
        return iwebby.IMapWidget(self.groupConversation
                ).setMapBackgroundFromChannel()

    def command_MAPDIGEST(self, command, args):
        ## # start queueing other commands until ENDDIGEST
        ## self.receivingDigest = True
        return defer.succeed(None)

    def command_ENDDIGEST(self, command, args):
        ## # stop queueing
        ## self.receivingDigest = False
        ## # release backlogged messages
        ## for deferred, meth, command, args in backlog:
        ##     try:
        ##         r = meth(command, args))
        ##         return d.callback(r)
        ##     except Exception, e:
        ##         return d.errback(e)
        return defer.succeed(None)

    def command_OBSCUREALL(self, command, args):
        return iwebby.IMapWidget(self.groupConversation
                ).updateObscurementFromChannel()

    def command_REVEALALL(self, command, args):
        return iwebby.IMapWidget(self.groupConversation
                ).updateObscurementFromChannel()


class MinConversation(
        basechat.Conversation,
        components.Componentized):
    """This class is a minimal implementation of the abstract Conversation class.

    This is all you need to override to receive one-on-one messages.
    """
    def __init__(self, widget, *a, **kw):
        components.Componentized.__init__(self)
        basechat.Conversation.__init__(self, *a, **kw)
        self.widget = widget

        self.setComponent(IChatFormatter, ChatFormatter())

    def show(self):
        pname = unicode(self.person.name)
        iwebby.IChatConversations(self.widget).showConversation(self, pname)
    
    def hide(self):
        pname = unicode(self.person.name)
        iwebby.IChatConversations(self.widget).hideConversation(self, pname)

    def showMapCommand(self, command, channel, args):
        """
        Using the channel from the args, get the groupconversation for the
        indicated map and process the command through that groupconversation.
        """
        # look up the groupConversation
        # OMG this is tedious.
        client = conversation.person.account.client
        chatui = conversation.chatui
        group = chatui.getGroup(channel.lstrip('#'), client) 
        mapconv = chatui.getGroupConversation(group)

        return mapconv.showMapCommand(command, channel, args)

    def showMessage(self, text, metadata=None):
        """
        Handle text received from the IRC server by printing it in my GUI
        """
        fmtd = IChatFormatter(self).format(text, sender=self.person.name,
                metadata=metadata)
        return iwebby.ITextArea(self).printClean(fmtd)

    def sendText(self, text, metadata=None):
        """
        Handle text that was sent by my client by sending it to the IRC server
        and printing it in the local client gui
        """
        r = self.person.sendMessage(text, metadata)
        me = self.person.account.client.name
        fmtd = IChatFormatter(self).format(text, sender=me, metadata=metadata)
        iwebby.ITextArea(self).printClean(fmtd)

        return r

    def contactChangedNick(self, person, newnick):
        basechat.Conversation.contactChangedNick(self, person, newnick)
        event = "-!- %s is now known as %s" % (person.name, newnick)
        return iwebby.ITextArea(self).printClean(event)


class MinGroupConversation(
        basechat.GroupConversation,
        components.Componentized):
    """This class is a minimal implementation of the abstract
    GroupConversation class.

    This is all you need to override to listen in on a group conversation.
    """
    def __init__(self, widget, *a, **kw):
        components.Componentized.__init__(self)
        basechat.GroupConversation.__init__(self, *a, **kw)
        self.widget = widget

        self.noticeParser = ReceivedNoticeParser(self)

        self.setComponent(IChatFormatter, ChatFormatter())

    def show(self):
        groupname = unicode('#' + self.group.name)
        iwebby.IChatConversations(self.widget).showConversation(self, groupname)

    def hide(self):
        groupname = unicode('#' + self.group.name)
        iwebby.IChatConversations(self.widget).hideConversation(self, groupname)

    def showMapCommand(self, command, channel,  args):
        return self.noticeParser.parse(command, channel, args)

    def showGroupMessage(self, sender, text, metadata=None):
        fmtd = IChatFormatter(self).format(text, sender=sender,
                metadata=metadata)
        return iwebby.ITextArea(self).printClean(fmtd)

    def sendText(self, text, metadata=None):
        r = self.group.sendGroupMessage(text, metadata)
        me = self.group.account.client.name
        fmtd = IChatFormatter(self).format(text, sender=me, metadata=metadata)
        iwebby.ITextArea(self).printClean(fmtd)
        return r

    def setTopic(self, topic, author):
        event = "-!- %s set the topic to: %s" % (author, topic)
        t = '%s (set by %s)' % (topic, author)
        iwebby.ITopicBar(self).setTopic(t)
        return iwebby.ITextArea(self).printClean(event)

    def setGroupMembers(self, names):
        return iwebby.INameSelect(self).setNames(names)

    def memberJoined(self, member):
        basechat.GroupConversation.memberJoined(self, member)
        event = "-!- %s joined #%s" % (member, self.group.name)
        iwebby.INameSelect(self).addName(member, None)
        return iwebby.ITextArea(self).printClean(event)

    def memberChangedNick(self, oldnick, newnick):
        basechat.GroupConversation.memberChangedNick(self, oldnick, newnick)
        event = "-!- %s is now known as %s in #%s" % (oldnick, newnick,
            self.group.name)
        namesel = iwebby.INameSelect(self)
        namesel.removeName(oldnick)
        namesel.addName(newnick, None)
        return iwebby.ITextArea(self).printClean(event)

    def memberLeft(self, member):
        basechat.GroupConversation.memberLeft(self, member)
        event = "-!- %s left #%s" % (member, self.group.name)
        iwebby.INameSelect(self).removeName(member)
        return iwebby.ITextArea(self).printClean(event)


class NoUIConnected(Exception):
    pass

    
class MinChat(basechat.ChatUI):
    """This class is a minimal implementation of the abstract ChatUI class.

    There are only two methods that need overriding - and of those two, 
    the only change that needs to be made is the default value of the Class
    parameter.
    """

    readyToChat = False

    def initUI(self, widget):
        self.readyToChat = True
        self.widget = widget
        self.groupClass = lambda *a, **kw: MinGroupConversation(widget, *a, **kw)
        self.convoClass = lambda *a, **kw: MinConversation(widget, *a, **kw)

    def getGroupConversation(self, group, Class=None, stayHidden=0):
        Class = Class or self.groupClass
        if not self.readyToChat:
            raise NoUIConnected()
        conv = self.groupConversations.get(group)
        if not conv:
            conv = Class(group, self)
            self.groupConversations[group] = conv
        return conv

    def getConversation(self, person, Class=None, stayHidden=0):
        if not self.readyToChat:
            raise NoUIConnected()
        conv = basechat.ChatUI.getConversation(self, person, self.convoClass, 
                stayHidden)
        return conv
