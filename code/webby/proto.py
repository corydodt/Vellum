"""
Implement the CLIENT-SIDE low-level IRC protocol.  Objects in here communicate
directly with an IRC server.
"""
from twisted.words.im import ircsupport, basesupport
from twisted.internet import defer, protocol, reactor
from twisted.words.protocols import irc

class WebbyProto(ircsupport.IRCProto):
    def connectionLost(self, reason):
        """
        Basically, t.words.im.basesupport.AbstractClientMixin is completely
        *fucked* in the head.  Subclassing it is impossible, because of the
        stupid fucking self._protoBase, which turns out to be IRCProto, not
        this class.

        I think what's happening is this proto instance has its connectionLost
        called, then IRCProto.connectionLost(self) *also* gets called.

        So, clobber connectionLost and do it ourselves, because that's fucking
        retarded.
        """
        self.account._clientLost(self, reason)
        self.unregisterAsAccountClient()
        return irc.IRCClient.connectionLost(self, reason)

    def parseCommand(self, text):
        """
        @return: a 3-tuple of command, channel, args
        """
        splits = text.split(None, 2)
        command = splits.pop(0)
        channel = splits.pop(0)
        if splits:
            rest = splits[0]
        else:
            rest = ''

        return command, channel, rest

    def noticed(self, username, channel, message):
        username = username.split('!', 1)[0]
        if username == self.name:
            return

        # notices from VellumTalk are always special commands for the map
        if username.lower() == 'vellumtalk':
            command, channel, args = self.parseCommand(message)
            if channel[0] == '#':
                group = channel[1:]
                conv = self.getGroupConversation(group, 
                        hide=True)
                conv.showMapCommand(command, channel, args)
                return
            # FIXME - parse, get the right group here, and use
            # groupconv.showMapCommand
            conv = self.chat.getConversation(self.getPerson(username),
                    hide=True)
            conv.showMapCommand(command, channel, args)
        else:
            # just a regular notice
            metadata = {'dontAutoRespond': True}

            if channel[0] == '#':
                group = channel[1:]
                self.getGroupConversation(group).showGroupMessage(username, 
                        message, metadata)
                return
            self.chat.getConversation(self.getPerson(username)).showMessage(
                    message, metadata)

    def lineReceived(self, line):
        print line
        return ircsupport.IRCProto.lineReceived(self, line)

    def joined(self, channel):
        print "Joining %s" % channel
        conv = self.getGroupConversation(channel.lstrip('#'))
        return conv.show()

    def left(self, channel):
        print "Left %s" % channel
        conv = self.getGroupConversation(channel.lstrip('#'), 1)
        return conv.hide()

    def userJoined(self, nickname, group):
        groupName = group.lstrip('#')
        try:
            self._ingroups[nickname].append(groupName)
        except:
            self._ingroups[nickname] = [groupName]
        self.getGroupConversation(groupName).memberJoined(nickname)

    def userLeft(self, nickname, group):
        groupName = group.lstrip('#')
        if groupName in self._ingroups[nickname]:
            self._ingroups[nickname].remove(groupName)
            self.getGroupConversation(groupName).memberLeft(nickname)
        else:
            print "%s left %s, but wasn't in the room."%(nickname,group)

    def userQuit(self, nickname, group):
        if self._ingroups.has_key(nickname):
            for group in self._ingroups[nickname]:
                self.getGroupConversation(group).memberLeft(nickname)
            self._ingroups[nickname] = []
        else:
            print '*** WARNING: ingroups had no such key %s' % nickname

    def irc_JOIN(self, prefix, params):

        #IRCProto makes me sad.  Lets not use it here
        return irc.IRCClient.irc_JOIN(self, prefix, params)

    def irc_PART(self, prefix, params):

        #IRCProto makes me sad.  Lets not use it here
        return irc.IRCClient.irc_PART(self, prefix, params)

    def irc_QUIT(self, prefix, params):

        #IRCProto makes me sad.  Lets not use it here
        return irc.IRCClient.irc_QUIT(self, prefix, params)

    def getGroupConversation(self, group, hide=0):
        return ircsupport.IRCProto.getGroupConversation(self, group.lstrip('#'), hide)

    def joinGroup(self, name):
        self.join(name)

    def leaveGroup(self, name):
        self.leave(name)

    def irc_333(self, prefix, params):
        group = params[1][1:]
        topic = self._topics.get(group, '')
        self.getGroupConversation(group).setTopic(topic, params[2])
        if self._topics.has_key(group):
            del self._topics[group]


class WebbyGroup(ircsupport.IRCGroup):
    def join(self):
        return basesupport.AbstractGroup.join(self)

    def leave(self):
        return basesupport.AbstractGroup.leave(self)


class WebbyAccount(ircsupport.IRCAccount):
    _groupFactory = WebbyGroup

    def _startLogOn(self, chatui):
        logonDeferred = defer.Deferred()
        cc = protocol.ClientCreator(reactor, WebbyProto, self, chatui,
                                    logonDeferred)
        d = cc.connectTCP(self.host, self.port)
        d.addErrback(logonDeferred.errback)
        return logonDeferred

    def joinGroups(self, groups):
        for group in groups:
            name = group.lstrip('#')
            self.getGroup(name).join()

    def leaveGroups(self, groups):
        for group in groups:
            name = group.lstrip('#')
            self.getGroup(name).leave()
