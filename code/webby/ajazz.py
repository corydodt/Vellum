from twisted.python.util import sibpath
from twisted.python import components
from twisted.internet import defer

from zope.interface import implements

from nevow import rend, loaders, athena, url, static

from webby import minchat, tabs, parseirc, windowing, util
from webby.minchat import IChatConversations, \
                          IChatEntry, \
                          IChatAccountManager, \
                          ITopicBar, \
                          ITextArea, \
                          INameSelect

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



class TopicBar(util.RenderWaitLiveElement):
    implements(ITopicBar)
    docFactory = loaders.xmlfile(RESOURCE('elements/TopicBar'))
    jsClass = u'WebbyVellum.TopicBar'

    def setTopic(self, topic):
        topic = unicode(topic)
        return self.callRemote('setTopic', topic)


class NameSelect(athena.LiveElement):
    implements(INameSelect)
    docFactory = loaders.xmlfile(RESOURCE('elements/NameSelect'))

NODEFAULT = object()

class ConversationTabs(tabs.TabsElement):
    ## jsClass = u"WebbyVellum.ConversationTabs"
    implements(IChatConversations)

    def __init__(self, *a, **kw):
        super(ConversationTabs, self).__init__(*a, **kw)
        self.conversations = {}

    def getConversation(self, id, default=NODEFAULT):
        """
        Get the IRC conversation object by the tab id
        """
        if default is NODEFAULT:
            return self.conversations[id]
        else:
            return self.conversations.get(id, default)
    
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
        ta = windowing.TextArea()
        ta.setFragmentParent(self)
        ta.setInitialArguments(GREETING)

        nullconv.setComponent(ITextArea, ta)


        self.conversations[initialId] = nullconv

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
        if cn not in self.conversations:
            # create a Container to hold the contents of the tab
            co = windowing.Container()
            co.setFragmentParent(self)

            # space for the topic
            tb = TopicBar()
            tb.setFragmentParent(co)

            # create the corresponding names list
            ns = NameSelect()
            ns.setFragmentParent(co)

            # create a textarea around the conversation
            ta = windowing.TextArea()
            ta.setFragmentParent(self)

            # assign components
            conversation.setComponent(ITextArea, ta)
            conversation.setComponent(ITopicBar, tb)
            conversation.setComponent(INameSelect, ns)

            co.addWidget(tb)
            co.addWidget(ta)
            co.addWidget(ns)

            d = self.addTab(cn, cn)

            def _added(ignored):
                return self.setTabBody(cn, co)

            d.addCallback(_added)

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

            def irccmdFallback(message, conv):
                strCommand = parsed.commandWord.encode('utf8').upper()
                message = '%s %s' % (strCommand, message)
                return self.irccmd_raw(message, conv)
                
            m = getattr(self, 
                        'irccmd_%s' % (parsed.commandWord,),
                        irccmdFallback)
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

        ## acct = conv.group.account
        # We're using this way to get the account because I can't figure out a
        # way to make it so all conversations have access to the account.  I
        # don't know if this will work.  FIXME
        acct = self.page.chatui.onlineClients[0].account

        if groups:
            args = args[len(groups[0])-1:].lstrip()
            groups = groups[0].split(',')

        acct.joinGroups(groups)

    irccmd_j = irccmd_join

    def irccmd_topic(self, args, conv):
        client = self.page.chatui.onlineClients[0]

        channel = None

        # see if the user is trying to see/set the topic for some other 
        # channel.  This applies if the first word begins with a hash #.
        if args.strip() != '':
            firstArg = args.split()[0]
            if firstArg[0] == '#':
                # remove the channel.
                args = args[len(firstArg):]
                args = args.lstrip()
                channel = firstArg

        if channel is None:
            if hasattr(conv, 'group'):
                channel = conv.group.name
            else:
                return conv.sendText("Cannot set or view topic of SERVER tab")

        channel = channel.lstrip('#')

        if args.strip() == '':
            args = None
        
        client.topic(channel, args)

    def irccmd_part(self, args, conv):
        groups = args.split()

        ## acct = conv.group.account
        # We're using this way to get the account because I can't figure out a
        # way to make it so all conversations have access to the account.  I
        # don't know if this will work.
        acct = self.page.chatui.onlineClients[0].account

        if groups:
            args = args[len(groups[0])-1:].lstrip()
            groups = groups[0].split(',')
        else:
            if hasattr(conv, 'group'):
                groups.append(conv.group.name.lstrip('#'))
            else:
                return conv.sendText("Cannot /part from SERVER tab")

        # TODO: Find out how to support parting messages
        acct.leaveGroups(groups)

    irccmd_leave = irccmd_part

    def irccmd_raw(self, args, conv):
        ## acct = conv.group.account
        # We're using this way to get the account because I can't figure out a
        # way to make it so all conversations have access to the account.  I
        # don't know if this will work.
        acct = self.page.chatui.onlineClients[0].account
        return acct.client.sendLine(args)

    def irccmd_query(self, args, conv):
        try:
            personName = args.split()[0]
            mesg = args[len(personName):].lstrip()
            chatui = self.page.chatui
            client = chatui.onlineClients[0]
            newConv = chatui.getConversation(chatui.getPerson(personName, client))
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
