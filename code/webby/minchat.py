"""Chat functionality"""

from twisted.words.im import basechat, baseaccount
from twisted.internet import defer, protocol, reactor

from twisted.words.im import ircsupport 

ACCOUNTS = {}

PROTOS = {}

IRCPORT = 6667

class VellumIRCProto(ircsupport.IRCProto):
    def irc_RPL_ENDOFNAMES(self,prefix,params):
        """Fixes a bug in the upstream implementation - the upstream strips
        off the # from the group name!
        """
        group=params[1][:]
        self.getGroupConversation(group).setGroupMembers(self._namreplies[group.lower()])
        del self._namreplies[group.lower()]

    def irc_JOIN(self,prefix,params):
        nickname = prefix.split("!")[0]
        group = params[0][:].lower()
        if nickname != self.nickname:
            try:
                self._ingroups[nickname].append(group)
            except:
                self._ingroups[nickname] = [group]
            self.getGroupConversation(group).memberJoined(nickname)

    def irc_RPL_NAMREPLY(self,prefix,params):
        """
        Same as above.

        RPL_NAMREPLY
        >> NAMES #bnl
        << :Arlington.VA.US.Undernet.Org 353 z3p = #bnl :pSwede Dan-- SkOyg AG
        """
        group=params[2][:].lower()
        users=params[3].split()
        for ui in range(len(users)):
            while users[ui][0] in ["@","+"]: # channel modes
                users[ui]=users[ui][1:]
        if not self._namreplies.has_key(group):
            self._namreplies[group]=[]
        self._namreplies[group].extend(users)
        for nickname in users:
                try:
                    self._ingroups[nickname].append(group)
                except:
                    self._ingroups[nickname]=[group]

    def irc_333(self,prefix,params):
        """
        Same as above.
        """
        group=params[1][:]
        self.getGroupConversation(group).setTopic(self._topics[group],params[2])
        del self._topics[group]

    def irc_RPL_TOPIC(self,prefix,params):
        """
        Same as above.
        """
        self._topics[params[1][:]]=params[2]

    def privmsg(self, username, channel, message, metadata=None):
        """Same as above."""
        if metadata is None:
            metadata = {}
        username = username.split('!', 1)[0]
        if username == self.name: return
        if channel[0] == '#':
            group = channel[:]
            self.getGroupConversation(group).showGroupMessage(username, message, metadata)
            return
        self.chat.getConversation(self.getPerson(username)).showMessage(message, metadata)
        
class VellumIRCAccount(ircsupport.IRCAccount):
    def _startLogOn(self, chatui):
        """Rape/paste from ircsupport to use VellumIRCProto instead.
        """
        logonDeferred = defer.Deferred()
        cc = protocol.ClientCreator(reactor, VellumIRCProto, self, chatui,
                                    logonDeferred)
        d = cc.connectTCP(self.host, self.port)
        d.addErrback(logonDeferred.errback)
        return logonDeferred

class AccountManager(baseaccount.AccountManager):
    """This class is a minimal implementation of the Acccount Manager.

    Most implementations will show some screen that lets the user add and
    remove accounts, but we're not quite that sophisticated.
    """

    def __init__(self, chatui):
        self.chatui = chatui


    def doConnection(self, username, password, host, channels):
        if username in ACCOUNTS and ACCOUNTS[username].isOnline():
            self.disconnect(ACCOUNTS[username])

        acct = VellumIRCAccount("IRC", 1, username, password, host,
                IRCPORT, channels)
        ACCOUNTS[username] = acct
        dl = []
        for acct in ACCOUNTS.values():
            d = acct.logOn(self.chatui)
            def _addProto(proto, self, acct):
                PROTOS[acct.username] = proto
                return acct
            d.addCallback(_addProto, self, acct)
            dl.append(d)

        return defer.DeferredList(dl)
        
    def disconnect(self, username):
        PROTOS[username].transport.loseConnection()



class MinConversation(basechat.Conversation):
    """This class is a minimal implementation of the abstract Conversation class.

    This is all you need to override to receive one-on-one messages.
    """
    def __init__(self, widget, *a, **kw):
        basechat.Conversation.__init__(self, *a, **kw)
        self.webPrint = lambda m: widget.printclean(self.user.name, m) 

    def show(self):
        """If you don't have a GUI, this is a no-op.
        """
        if self.user.name in self.widget.conversations:
            self.widget.foregroundConversation = self
            self.widget.callRemote("show", unicode(self.user.name))
    
    def hide(self):
        """If you don't have a GUI, this is a no-op.
        """
    
    def showMessage(self, text, metadata=None):
        event = "<%s> %s" % (self.person.name, text)
        return self.webPrint(event)
        
    def contactChangedNick(self, person, newnick):
        basechat.Conversation.contactChangedNick(self, person, newnick)
        event = "-!- %s is now known as %s" % (person.name, newnick)
        return self.webPrint(event)


class MinGroupConversation(basechat.GroupConversation):
    """This class is a minimal implementation of the abstract
    GroupConversation class.

    This is all you need to override to listen in on a group conversation.
    """
    def __init__(self, widget, *a, **kw):
        basechat.GroupConversation.__init__(self, *a, **kw)
        self.widget = widget
        self.webPrint = lambda m: widget.printClean(self.group.name, m)

    def show(self):
        """If you don't have a GUI, this is a no-op.
        """
        if self.group.name in self.widget.conversations:
            self.widget.foregroundConversation = self
            self.widget.callRemote("show", unicode(self.group.name))

    def hide(self):
        """If you don't have a GUI, this is a no-op.
        """
        pass

    def showGroupMessage(self, sender, text, metadata=None):
        t = "<%s> %s" % (sender, text)
        return self.webPrint(t)

    def setTopic(self, topic, author):
        event = "-!- %s set the topic to: %s" % (author, topic)
        return self.webPrint(event)
                

    def memberJoined(self, member):
        basechat.GroupConversation.memberJoined(self, member)
        event = "-!- %s joined %s" % (member, self.group.name)
        return self.webPrint(event)

    def memberChangedNick(self, oldnick, newnick):
        basechat.GroupConversation.memberChangedNick(self, oldnick, newnick)
        event = "-!- %s is now known as %s in %s" % (oldnick, newnick,
            self.group.name)
        return self.webPrint(event)

    def memberLeft(self, member):
        basechat.GroupConversation.memberLeft(self, member)
        event = "-!- %s left %s" % (member, self.group.name)
        return self.webPrint(event)

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
        if not self.readyToChat:
            raise NoUIConnected()
        conv = basechat.ChatUI.getGroupConversation(self, group, self.groupClass, 
            stayHidden)
        return conv

    def getConversation(self, person, Class=None, stayHidden=0):
        if not self.readyToChat:
            raise NoUIConnected()
        conv = basechat.ChatUI.getConversation(self, person, self.convoClass, 
                stayHidden)
        return conv
