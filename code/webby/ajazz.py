from twisted.python.util import sibpath
from nevow import tags as T, rend, loaders, athena, url, static, flat

import minchat
import tabs
import parseirc

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

class IRCContainer(athena.LiveFragment):
    jsClass = u"WebbyVellum.IRCContainer"
    docFactory = loaders.xmlfile(RESOURCE('fragments/IRCContainer'))
    def __init__(self, 
                 accountManagerFragment, 
                 conversationFragment,
                 chatEntry,
                 *a, **kw):
        athena.LiveFragment.__init__(self, *a, **kw)
        self.conversationFragment = conversationFragment
        self.accountManagerFragment = accountManagerFragment
        self.chatEntry = chatEntry

    def render_irc(self, ctx, data):
        return ctx.tag[
                self.accountManagerFragment,
                self.conversationFragment,
                self.chatEntry,
                ]

class ConversationWindow(tabs.TabsFragment):
    ## jsClass = u"WebbyVellum.ConversationWindow"

    def __init__(self, *a, **kw):
        super(ConversationWindow, self).__init__(*a, **kw)
        self.conversations = {}
    
    def printClean(self, id, message):
        self.callRemote('appendToTab', webClean(id), flattenMessageString(message))

    def showConversation(self, conversation, conversationName):
        cn = unicode(conversationName)
        if cn not in self.conversations:
            self.addTab(cn, cn)
        self.conversations[cn] = conversation
        self.callRemote("show", cn)

    def getInitialArguments(self):
        return (u'SERVER', u'SERVER', 
                flattenMessageString(
u'''Vellum IRC v0.0
Click Log ON to connect.'''
                    ))

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
        d.addCallback(lambda account: True)
        return d
    athena.expose(onLogOnSubmit)

    jsClass = u"WebbyVellum.AccountManager"

class ChatEntry(athena.LiveFragment):
    docFactory = loaders.xmlfile(RESOURCE('fragments/ChatEntry'))

    jsClass = u"WebbyVellum.ChatEntry"

    def __init__(self, chatui, *a, **kw):
        super(ChatEntry, self).__init__(*a, **kw)
        self.chatui = chatui

    def chatMessage(self, message, tabid):
        w = self.chatui.widget
        parsed = parseirc.line.parseString(message)
        conv = w.conversations[tabid]
        if parsed.command:
            m = getattr(self, 'irccmd_%s' % (parsed.commandWord,))
            m(conv, parsed.commandArgs)
        else:
            conv.sendText(parsed.nonCommand[0].encode('utf8'))
    athena.expose(chatMessage)

    def irccmd_me(self, conversation, args):
        conversation.sendText(args, metadata={'style':'emote'})



class LiveVellum(athena.LivePage):
    addSlash = True

    docFactory = loaders.xmlfile(RESOURCE('webby.xhtml'))
    def __init__(self, *a, **kw):
        super(LiveVellum, self).__init__(*a, **kw)
        self.jsModules.mapping[u'WebbyVellum'] = RESOURCE('webby.js')
        self.jsModules.mapping[u'Tabby'] = RESOURCE('tabby.js')
        self.chatui = minchat.MinChat()
        self.accountManager = minchat.AccountManager(self.chatui)


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
        cw = ConversationWindow()
        cw.page = self
        # chatui.initUI hooks this conversation window up
        self.chatui.initUI(cw)

        am = AccountManagerFragment(self.accountManager, cw)
        am.page = self

        ce = ChatEntry(chatui=self.chatui)
        ce.page = self

        irc = IRCContainer(am, cw, ce)
        irc.page = self

        return ctx.tag[irc]
