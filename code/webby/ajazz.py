from twisted.python.util import sibpath
from twisted.python import components
from twisted.internet import defer

from zope.interface import implements

from nevow import tags as T, rend, loaders, athena, url, static, flat

from webby import minchat, tabs, parseirc
from webby.minchat import IChatConversations, IChatEntry, IChatAccountManager

RESOURCE = lambda f: sibpath(__file__, f)

class WVRoot(rend.Page):
    addSlash = True
    def child__(self, ctx, ):
        return LiveVellum()

    def child_css(self, ctx, ):
        return static.File(RESOURCE('webby.css'))

    def renderHTTP(self, ctx):
        return url.root.child("_")


class Map(athena.LiveFragment):
    docFactory = loaders.stan(['map'])

class Minimap(Map):
    ## jsClass = u"WebbyVellum.Minimap"
    docFactory = loaders.xmlfile(RESOURCE('fragments/Minimap'))

class Mainmap(Map):
    ## jsClass = u"WebbyVellum.Mainmap"
    docFactory = loaders.xmlfile(RESOURCE('fragments/Mainmap'))


class IRCContainer(athena.LiveFragment, components.Componentized):
    jsClass = u"WebbyVellum.IRCContainer"
    docFactory = loaders.xmlfile(RESOURCE('fragments/IRCContainer'))

    def __init__(self, accountManager, *a, **kw):
        athena.LiveFragment.__init__(self, *a, **kw)
        components.Componentized.__init__(self)
        cw = ConversationWindow()
        cw.setInitialArguments(u'**SERVER**', u'**SERVER**', 
                flattenMessageString(
u'''Vellum IRC v0.0
Click Log ON to connect.'''
                    ))
        cw.setFragmentParent(self)
        self.setComponent(IChatConversations, cw)

        am = AccountManagerFragment(accountManager, cw)
        am.setFragmentParent(self)
        self.setComponent(IChatAccountManager, am)

        ce = ChatEntry()
        ce.setFragmentParent(self)
        self.setComponent(IChatEntry, ce)

    def render_irc(self, ctx, data):
        return ctx.tag[
                IChatAccountManager(self),
                IChatConversations(self),
                IChatEntry(self),
                ]



NODEFAULT = object()

class ConversationWindow(tabs.TabsFragment):
    ## jsClass = u"WebbyVellum.ConversationWindow"
    implements(IChatConversations)

    def __init__(self, *a, **kw):
        super(ConversationWindow, self).__init__(*a, **kw)
        self.conversations = {}

    def getConversation(self, id, default=NODEFAULT):
        if default is NODEFAULT:
            return self.conversations[id]
        else:
            return self.conversations.get(id, default)
    
    def printClean(self, message, id):
        self.callRemote('appendToTab', webClean(id), flattenMessageString(message))

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

def webClean(st):
    return unicode(st.replace('<','&lt;').replace('>','&gt;'))

def flattenMessageString(st):
    """Return a string suitable for serializing over to a tab pane."""
    span = T.span(xmlns="http://www.w3.org/1999/xhtml")
    for line in st.splitlines():
        span[line, T.br]
    return unicode(flat.flatten(span))

class AccountManagerFragment(athena.LiveFragment):
    docFactory = loaders.xmlfile(RESOURCE('fragments/AccountManagerFragment'))
    implements(IChatAccountManager)

    def __init__(self, accountManager, conversationWindow, *a, **kw):
        super(AccountManagerFragment, self).__init__(*a, **kw)
        self.accountManager = accountManager
        self.conversationWindow = conversationWindow

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

class ChatEntry(athena.LiveFragment):
    docFactory = loaders.xmlfile(RESOURCE('fragments/ChatEntry'))
    implements(IChatEntry)

    jsClass = u"WebbyVellum.ChatEntry"

    def chatMessage(self, message, tabid):
        conv = IChatConversations(self.fragmentParent).getConversation(tabid, None)

        parsed = parseirc.line.parseString(message)
        if parsed.command:
            m = getattr(self, 'irccmd_%s' % (parsed.commandWord,))
            m(parsed.commandArgs.encode('utf8'), conv)
        else:
            self.say(parsed.nonCommand[0].encode('utf8'), conv)
    athena.expose(chatMessage)

    def say(self, message, conv):
        # TODO - if conv is None: ...
        conv.sendText(message)

    def irccmd_me(self, args, conv):
        # TODO - if conv is None: ...
        conv.sendText(args, metadata={'style':'emote'})



class LiveVellum(athena.LivePage):
    addSlash = True

    docFactory = loaders.xmlfile(RESOURCE('webby.xhtml'))
    def __init__(self, *a, **kw):
        super(LiveVellum, self).__init__(*a, **kw)
        self.chatui = minchat.MinChat()


    def render_debug(self, ctx, data):
        f = athena.IntrospectionFragment()
        f.setFragmentParent(self)
        return ctx.tag[f]

    def render_minimap(self, ctx, data):
        m = Minimap()
        m.page = self
        return ctx.tag[m]

    def render_mainmap(self, ctx, data):
        m = Mainmap()
        m.page = self
        return ctx.tag[m]

    def render_chat(self, ctx, data):
        accountManager = minchat.AccountManager(self.chatui)
        irc = IRCContainer(accountManager)
        irc.page = self

        self.chatui.initUI(irc)

        return ctx.tag[irc]
