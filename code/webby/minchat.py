"""Chat functionality"""

from twisted.words.im import basechat, baseaccount, ircsupport
from twisted.internet import defer, protocol, reactor
from twisted.python import components

from webby.proto import WebbyAccount # Using custom account, so as to use a custom protocol
from webby import iwebby
from webby.iwebby import * # TODO - remove this and fix importers from minchat

ACCOUNTS = {}

PROTOS = {}

IRCPORT = 6667

class AccountManager(baseaccount.AccountManager):
    """This class is a minimal implementation of the Acccount Manager.

    Most implementations will show some screen that lets the user add and
    remove accounts, but we're not quite that sophisticated.
    """

    def __init__(self, chatui):
        self.chatui = chatui

    def doConnection(self, host, username, password, channels):
        key = (username, host)
        if key in ACCOUNTS and ACCOUNTS[key].isOnline():
            self.disconnect(ACCOUNTS[key])

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
        
    def disconnect(self, account):
        key = (account.username, account.host)
        PROTOS[key].transport.loseConnection()
        del PROTOS[key]
        del ACCOUNTS[key]


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

    def show(self):
        pname = unicode(self.person.name)
        iwebby.IChatConversations(self.widget).showConversation(self, pname)
    
    def hide(self):
        pname = unicode(self.person.name)
        iwebby.IChatConversations(self.widget).hideConversation(self, pname)
    
    def showMessage(self, text, metadata=None):
        return self._reallyShowMessage(self.person.name, text, metadata)

    def _reallyShowMessage(self, name, text, metadata):
        if metadata is None: metadata = {}

        if metadata.get("style", None) == "emote":
            t = '* %s %s' % (name, text)
        elif metadata.get('dontAutoRespond', None):
            t = "-%s- %s" % (name, text)
        else:
            t = "<%s> %s" % (name, text)

        return iwebby.ITextArea(self).printClean(t)

    def sendText(self, text, metadata=None):
        r = self.person.sendMessage(text, metadata)
        me = self.person.account.client.name
        self._reallyShowMessage(me, text, metadata)

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

    def show(self):
        groupname = unicode('#' + self.group.name)
        iwebby.IChatConversations(self.widget).showConversation(self, groupname)

    def hide(self):
        groupname = unicode('#' + self.group.name)
        iwebby.IChatConversations(self.widget).hideConversation(self, groupname)

    def showGroupMessage(self, sender, text, metadata=None):
        return self._reallyShowMessage(sender, text, metadata)

    def _reallyShowMessage(self, name, text, metadata):
        if metadata is None: metadata = {}

        if metadata.get("style", None) == "emote":
            t = '* %s %s' % (name, text)
        elif metadata.get('dontAutoRespond', None):
            t = "-%s- %s" % (name, text)
        else:
            t = "<%s> %s" % (name, text)

        return iwebby.ITextArea(self).printClean(t)

    def sendText(self, text, metadata=None):
        r = self.group.sendGroupMessage(text, metadata)
        me = self.group.account.client.name
        self._reallyShowMessage(me, text, metadata)

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
        event = "-!- %s joined %s" % (member, self.group.name)
        iwebby.INameSelect(self).addName(member, None)
        return iwebby.ITextArea(self).printClean(event)

    def memberChangedNick(self, oldnick, newnick):
        basechat.GroupConversation.memberChangedNick(self, oldnick, newnick)
        event = "-!- %s is now known as %s in %s" % (oldnick, newnick,
            self.group.name)
        namesel = iwebby.INameSelect(self)
        namesel.removeName(oldnick)
        namesel.addName(newnick, None)
        return iwebby.ITextArea(self).printClean(event)

    def memberLeft(self, member):
        basechat.GroupConversation.memberLeft(self, member)
        event = "-!- %s left %s" % (member, self.group.name)
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
