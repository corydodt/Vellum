from twisted.python.util import sibpath
from twisted.python import components
from twisted.internet import defer

from zope.interface import implements

from nevow import tags as T, rend, loaders, athena, url, static, flat

from webby import minchat, tabs, parseirc, windowing
from webby.minchat import IChatConversations, IChatEntry, IChatAccountManager

RESOURCE = lambda f: sibpath(__file__, f)

class WVRoot(rend.Page):
    addSlash = True
    def child__(self, ctx, ):
        return LiveVellum()

    def child_css(self, ctx, ):
        return static.File(RESOURCE('webby.css'))

    def child_tabs_css(self, ctx, ):
        return static.File(RESOURCE('tabs.css'))
    def renderHTTP(self, ctx):
        return url.root.child("_")



class IRCContainer(windowing.Enclosure, components.Componentized):
    jsClass = u"WebbyVellum.IRCContainer"

    def __init__(self, accountManager, *a, **kw):
        super(IRCContainer, self).__init__(
                windowTitle="IRC", userClass="irc", *a, **kw)
        components.Componentized.__init__(self)
        self.accountManager = accountManager

    def enclosedRegion(self, request, tag):
        cw = ConversationTabs()
        cw.setFragmentParent(self)
        self.setComponent(IChatConversations, cw)
        cw.setInitialArguments(u'**SERVER**', u'**SERVER**', GREETING)

        am = AccountManagerElement(self.accountManager, cw)
        am.setFragmentParent(self)
        self.setComponent(IChatAccountManager, am)

        ce = ChatEntry()
        ce.setFragmentParent(self)
        self.setComponent(IChatEntry, ce)
        return tag[am, cw, ce]
    athena.renderer(enclosedRegion)


class IRCTextArea(windowing.TextArea):
    docFactory = loaders.xmlfile(RESOURCE('elements/TextArea'))
    def __init__(self, conversation, *a, **kw):
        super(IRCTextArea, self).__init__(*a, **kw)
        self.conversation = conversation

NODEFAULT = object()

class ConversationTabs(tabs.TabsElement):
    ## jsClass = u"WebbyVellum.ConversationTabs"
    implements(IChatConversations)

    def __init__(self, *a, **kw):
        super(ConversationTabs, self).__init__(*a, **kw)
        self.conversations = {}

    def getConversation(self, id, default=NODEFAULT):
        if default is NODEFAULT:
            return self.conversations[id]
        else:
            return self.conversations.get(id, default)
    
    def printClean(self, message, id):
        id = webClean(id)
        message = flattenMessageString(message)
        return self.callRemote('appendToTab', id, message)
 
    def setInitialArguments(self, initialId, initialLabel, initialContent):
        super(ConversationTabs, self).setInitialArguments(
                initialId, initialLabel, initialContent)
        nullconv = minchat.NullConversation(self.fragmentParent, initialId)
        self.conversations[initialId] = nullconv

    def showConversation(self, conversation, conversationName):
        cn = unicode(conversationName)
        if cn not in self.conversations:
            d = self.addTab(cn, cn)
            self.conversations[cn] = conversation
        else:
            d = defer.succeed(None)

        def _conversationIsReady(_):
            return self.callRemote("show", cn)
        d.addCallback(_conversationIsReady)

        def _conversationFailed(e):
            del self.conversations[cn]
            return e
        d.addErrback(_conversationFailed)
        # FIXME - we do not return this deferred.  Need to see whether
        # minchat deals with deferreds returned by this stack

    def hideConversation(self, conversation, conversationName):
        cn = unicode(conversationName)
        if cn in self.conversations:
            d = self.removeTab(cn)
            del self.conversations[cn]
        else:
            d = defer.succeed(None)
        # FIXME - we do not return this deferred.  Need to see whether
        # minchat deals with deferreds returned by this stack

def webClean(st):
    return unicode(st.replace('<','&lt;').replace('>','&gt;'))

def flattenMessageString(st):
    """Return a string suitable for serializing over to a tab pane."""
    span = T.span(xmlns="http://www.w3.org/1999/xhtml")
    for line in st.splitlines():
        span[line, T.br]
    return unicode(flat.flatten(span))

GREETING = flattenMessageString(u'''Vellum IRC v0.0\nClick Log ON to connect.''')

class AccountManagerElement(athena.LiveElement):
    docFactory = loaders.xmlfile(RESOURCE('elements/AccountManagerElement'))
    implements(IChatAccountManager)

    def __init__(self, accountManager, conversationTabs, *a, **kw):
        super(AccountManagerElement, self).__init__(*a, **kw)
        self.accountManager = accountManager
        self.conversationTabs = conversationTabs

    def onLogOnSubmit(self, username, password, channels):
        host = 'localhost'.encode('utf8') # TODO - get from config file
        username = username.encode('utf8')
        password = password.encode('utf8')
        channels = channels.encode('utf8')
        d = self.accountManager.doConnection(host, username, password, channels)
        def _gotAccount(acct):
            return u'connected %s:%s@%s and joined %s' % (username, password, host, channels)
        d.addCallback(_gotAccount)
        return d
    athena.expose(onLogOnSubmit)

    jsClass = u"WebbyVellum.AccountManager"

class ChatEntry(athena.LiveElement):
    docFactory = loaders.xmlfile(RESOURCE('elements/ChatEntry'))
    implements(IChatEntry)

    jsClass = u"WebbyVellum.ChatEntry"

    def chatMessage(self, message, tabid):
        conv = IChatConversations(self.fragmentParent).getConversation(tabid)

        parsed = parseirc.line.parseString(message)
        if parsed.command:
            m = getattr(self, 'irccmd_%s' % (parsed.commandWord,))
            m(parsed.commandArgs.encode('utf8'), conv)
        else:
            self.say(parsed.nonCommand[0].encode('utf8'), conv)
        return None
    athena.expose(chatMessage)

    def say(self, message, conv):
        return conv.sendText(message)

    def irccmd_me(self, args, conv):
        return conv.sendText(args, metadata={'style':'emote'})

    def irccmd_join(self, args, conv):
        groups = args.split()

        if groups:
            args = args[len(groups[0])-1:].lstrip()
            acct = conv.group.account
            groups = groups[0].split(',')
            groups = [acct.getGroup(group.lstrip('#')) for group in groups]

        for group in groups:
            group.join()
    irccmd_j = irccmd_join

    def irccmd_part(self, args, conv):
        groups = args.split()
        ircgroups = []

        if groups:
            args = args[len(groups[0])-1:].lstrip()
            groups = groups[0].split(',')

            for group in groups:
                name = group.lstrip('#')
                if name in conv.group.account.channels:
                    ircgroups.append(conv.group.account.getGroup(name))
                else:
                    conv.sendText("Cannot /part from %s as it has not been joined." % group)

        if len(ircgroups) == 0:
            try:
                ircgroups.append(conv.group.account.getGroup(conv.group.name))
            except AttributeError:
                conv.sendText("Cannot /part from the SERVER tab, it is not a channel.")

        # TODO: Find out how to support parting messages

        for group in ircgroups:
            group.leave()
    irccmd_leave = irccmd_part

    def irccmd_raw(self, args, conv):
        return conv.group.account.client.sendLine(args)

class LiveVellum(athena.LivePage):
    addSlash = True

    docFactory = loaders.xmlfile(RESOURCE('webby.xhtml'))
    def __init__(self, *a, **kw):
        super(LiveVellum, self).__init__(*a, **kw)
        self.chatui = minchat.MinChat()

    def render_minimap(self, ctx, data):
        enc = windowing.Enclosure(windowTitle="Mini Map", userClass="minimap")
        enc.setFragmentParent(self)
        return ctx.tag[enc]

    def render_mainmap(self, ctx, data):
        enc = windowing.Enclosure(windowTitle="Main Map", userClass="mainmap")
        enc.setFragmentParent(self)
        return ctx.tag[enc]

    def render_chat(self, ctx, data):
        accountManager = minchat.AccountManager(self.chatui)
        irc = IRCContainer(accountManager)
        irc.setFragmentParent(self)

        self.chatui.initUI(irc)

        return ctx.tag[irc]
