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
    docFactory = loaders.xmlstr("""
    <div class="minimap"
         xmlns:n="http://nevow.com/ns/nevow/0.1"
         n:render="liveFragment">
         mini map
    </div>
    """)

class Mainmap(Map):
    docFactory = loaders.xmlstr("""
    <div class="mainmap"
         xmlns:n="http://nevow.com/ns/nevow/0.1"
         n:render="liveFragment">
         main map
    </div>
    """)

class ConversationWindow(tabs.TabsFragment):
    def __init__(self, *a, **kw):
        super(ConversationWindow, self).__init__(*a, **kw)
        self.conversations = {}
    
    def printClean(self, id, message):
        self.callRemote('appendToTab', webClean(id), flattenMessageString(message))

    def joinedConversation(self, conversation):
        name = unicode(conversation.name)
        self.addTab(name, name)
        self.conversations[name] = conversation

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
    docFactory = loaders.xmlstr("""
    <form xmlns:n="http://nevow.com/ns/nevow/0.1" 
        xmlns:athena="http://divmod.org/ns/athena/0.7"
        n:render="liveFragment">
        <athena:handler event="onclick" handler="onLogOnSubmit" />
        U: <input name="username" value="bot" class="corner" />
        P: <input name="password" value="ninjas" class="corner" />
        Channels: <input name="channels" value="#vellum" class="corner" />
        <input type="button" value="Log ON"  />
    </form>
    """)

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
        def _connectedAccounts(rl):
            for status, account in rl:
                if status:
                    for channel in account.channels:
                        group = account.getGroup(channel)
                        self.conversationWindow.joinedConversation(group)

        d.addCallback(_connectedAccounts)
        return d
    athena.expose(onLogOnSubmit)

    jsClass = u"WebbyVellum.AccountManager"

class ChatEntry(athena.LiveFragment):
    docFactory = loaders.xmlstr("""
    <p xmlns:n="http://nevow.com/ns/nevow/0.1"
       xmlns:athena="http://divmod.org/ns/athena/0.7"
       n:render="liveFragment"><athena:handler event="onkeyup" handler="checkEnter"
       /><input class="chatentry" /></p>
    """)

    jsClass = u"WebbyVellum.ChatEntry"

    def __init__(self, chatui, *a, **kw):
        super(ChatEntry, self).__init__(*a, **kw)
        self.chatui = chatui

    def chatMessage(self, message,):
        w = self.chatui.widget
        parsed = parseirc.line.parseString(message)
        conv = w.foregroundConversation
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
        c = ConversationWindow()
        c.page = self
        # chatui.initUI hooks this conversation window up
        self.chatui.initUI(c)

        am = AccountManagerFragment(self.accountManager, c)
        am.page = self

        ce = ChatEntry(chatui=self.chatui)
        ce.page = self

        return ctx.tag[am, c, ce]
