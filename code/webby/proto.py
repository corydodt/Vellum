from twisted.words.im import ircsupport, basesupport
from twisted.internet import defer, protocol, reactor
from twisted.words.protocols import irc

class WebbyProto(ircsupport.IRCProto):
    def lineReceived(self, line):
        print line
        return ircsupport.IRCProto.lineReceived(self, line)

    def joined(self, channel):
        print "Joining %s" % channel
        conv=self.getGroupConversation(channel.lstrip('#'))
        conv.show()

    def left(self, channel):
        print "Left %s" % channel
        conv=self.getGroupConversation(channel.lstrip('#'), 1)
        conv.hide()

    def userJoined(self, nickname, group):
        groupName = group.lstrip('#')
        try:
            self._ingroups[nickname].append(groupName)
        except:
            self._ingroups[nickname]=[groupName]
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
            self._ingroups[nickname]=[]
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
