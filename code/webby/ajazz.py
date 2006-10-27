from twisted.python.util import sibpath
from twisted.python import components
from twisted.internet import defer

from zope.interface import implements

from nevow import rend, loaders, athena, url, static

from webby import minchat, tabs, parseirc, windowing, util
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
        cw.initServerTab()

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
        self.textareas = {}

    def getConversation(self, id, default=NODEFAULT):
        """
        Get the IRC conversation object by the tab id
        """
        if default is NODEFAULT:
            return self.textareas[id].conversation
        else:
            return self.textareas.get(id, default).conversation
    
    def printClean(self, message, id):
        """
        Dispatch a print to the correct textarea.
        """
        id = webClean(id) # TODO - this should be used everywhere; need a
                          # better interface
        ta = self.textareas[id]
        return ta.printClean(message)
 
    def initServerTab(self):
        """
        Boilerplate for setting up an IRC tabs widget.

        This creates the server tab and null server conversation,
        connects them together, and sets up things so all of that will be sent
        together in the first render.
        """
        initialId = u'**SERVER**'

        nullconv = minchat.NullConversation(self.fragmentParent, initialId)

        # create a textarea around the conversation
        ta = IRCTextArea(nullconv)
        ta.setFragmentParent(self)
        ta.setInitialArguments(GREETING)

        self.textareas[initialId] = ta

        super(ConversationTabs, self).setInitialArguments(
                initialId, initialId, ta)

    def showConversation(self, conversation, conversationName):
        """
        Bring a conversation to the foreground.

        This is called whenever someone says something in that conversation.
        TODO: instead of bringing it to the foreground, display a 
        highlight marker when the conversation exists already.
        """
        cn = unicode(conversationName)
        if cn not in self.textareas:
            # create a textarea around the conversation
            ta = IRCTextArea(conversation)
            ta.setFragmentParent(self)

            d = self.addTab(cn, cn)

            def _added(ignored, textarea):
                return self.setTabBody(cn, textarea)

            d.addCallback(_added, ta)

            self.textareas[cn] = ta
        else:
            d = defer.succeed(None)

        def _conversationIsReady(_):
            return self.callRemote("show", cn)
        d.addCallback(_conversationIsReady)

        def _conversationFailed(e):
            del self.textareas[cn]
            return e
        d.addErrback(_conversationFailed)

        return d

    def hideConversation(self, conversation, conversationName):
        """
        Make a conversation disappear.
        """
        cn = unicode(conversationName)
        if cn in self.textareas:
            d = self.removeTab(cn)
            del self.textareas[cn]
        else:
            d = defer.succeed(None)
        # FIXME - we do not return this deferred.  Need to see whether
        # minchat deals with deferreds returned by this stack

def webClean(st):
    return unicode(st.replace('<','&lt;').replace('>','&gt;'))

GREETING = util.flattenMessageString(
u'''Vellum IRC v0.0
Click Log ON to connect.''')

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

        #acct = conv.group.account
        #We're using this way to get the account because I can't figure out a way to make
        #it so all conversations have access to the account.  I don't know if this will work.
        #FIXME
        acct = self.fragmentParent.fragmentParent.chatui.onlineClients[0].account

        if groups:
            args = args[len(groups[0])-1:].lstrip()
            groups = groups[0].split(',')

        acct.joinGroups(groups)
    irccmd_j = irccmd_join

    def irccmd_part(self, args, conv):
        groups = args.split()

        #acct = conv.group.account
        #We're using this way to get the account because I can't figure out a way to make
        #it so all conversations have access to the account.  I don't know if this will work.
        acct = self.fragmentParent.fragmentParent.chatui.onlineClients[0].account

        if groups:
            args = args[len(groups[0])-1:].lstrip()
            groups = groups[0].split(',')
        else:
            try:
                groups.append(conv.group.name.lstrip('#'))
            except AttributeError:
                conv.sendText("Cannot /part from SERVER tab")

        # TODO: Find out how to support parting messages
        acct.leaveGroups(groups)
    irccmd_leave = irccmd_part

    def irccmd_raw(self, args, conv):

        #acct = conv.group.account
        #We're using this way to get the account because I can't figure out a way to make
        #it so all conversations have access to the account.  I don't know if this will work.
        acct = self.fragmentParent.fragmentParent.chatui.onlineClients[0].account
        return acct.client.sendLine(args)

    def irccmd_query(self, args, conv):
        try:
            personName=args.split()[0]
            mesg=args[len(personName):].lstrip()
            chatui=self.fragmentParent.fragmentParent.chatui
            client=chatui.onlineClients[0]
            newConv=chatui.getConversation(chatui.getPerson(personName, client))
            newConv.show()
            if mesg:
                newConv.sendText(mesg)
        except:
                conv.sendText("Problems with /query, bailing out.")

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
