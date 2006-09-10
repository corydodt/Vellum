from twisted.python.util import sibpath
from nevow import tags as T, rend, loaders, athena, url, static

import minchat

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

class ConversationWindow(athena.LiveFragment):
    docFactory = loaders.xmlstr("""
    <div class="chatview"
         xmlns:n="http://nevow.com/ns/nevow/0.1"
         n:render="liveFragment">
    </div>
    """)

    jsClass = u"WebbyVellum.ConversationWindow"

    def __init__(self, *a, **kw):
        super(ConversationWindow, self).__init__(*a, **kw)
        self.conversations = {}

    def printClean(self, message):
        self.callRemote("showChatEvent", webClean(message))

    def joinedConversation(self, conversation):
        self.conversations[conversation.name] = conversation

def webClean(st):
    return unicode(st.replace('<','&lt;').replace('>','&gt;'))

class AccountManagerFragment(athena.LiveFragment):
    docFactory = loaders.xmlstr("""
    <form xmlns:n="http://nevow.com/ns/nevow/0.1" 
        xmlns:athena="http://divmod.org/ns/athena/0.7"
        n:render="liveFragment">
        <athena:handler event="onclick" handler="onLogOnSubmit" />
        <input name="host" value="localhost" />
        <input name="username" value="bot" />
        <input name="password" value="ninjas" />
        <input name="channels" value="#vellum" />
        <input type="button" value="Log ON" />
    </form>
    """)

    def __init__(self, accountManager, conversationWindow, *a, **kw):
        super(AccountManagerFragment, self).__init__(*a, **kw)
        self.accountManager = accountManager
        self.conversationWindow = conversationWindow

    def onLogOnSubmit(self, host, username, password, channels):
        host = host.encode('utf8')
        username = username.encode('utf8')
        password = password.encode('utf8')
        channels = channels.encode('utf8')
        d = self.accountManager.doConnection(host, username, password, channels)
        def _connectedAccounts(rl):
            for status, account in rl:
                if status:
                    for channel in account.channels:
                        import pdb; pdb.set_trace()
                        self.conversationWindow.joinedConversation(channel)

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

    def chatMessage(self, message):
        import pdb; pdb.set_trace()
        self.chatui.groupConversations.values()[0].sendText(message.encode('utf8'))
    athena.expose(chatMessage)


class LiveVellum(athena.LivePage):
    addSlash = True

    docFactory = loaders.xmlfile(RESOURCE('webby.xhtml'))
    def __init__(self, *a, **kw):
        super(LiveVellum, self).__init__(*a, **kw)
        self.jsModules.mapping[u'WebbyVellum'] = RESOURCE('webby.js')
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
