"""
Vellum's face.  The bot that answers actions in the channel.
"""
# system imports
import time, sys
import re
import traceback
import glob
from sets import Set

# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, task
from twisted.python import log


from vellum.server import encounter, alias, linesyntax
from vellum.server.fs import fs

class UnknownHailError(Exception):
    pass

class Session:
    def __init__(self, channel):
        self.channel = channel
        # TODO - move this into d20-specific code somewhere
        self.initiatives = []
        self.nicks = Set() # TODO - add a wrapper function for fixing bindings
                           # when nicks are removed or added
        alias.registerAliasHook(('init',), self.doInitiative)
        self.observers = Set()

    # def _loadParty(self):
    #    """Load characters in the party/ dir"""
    #    for filename in glob.glob(fs.party('*.yml')):
    #        char = encounter.Character(filename=fs.party(filename))
    #        self.party.addCharacter(char)

    # responses to being hailed by a user
    def respondTo_DEFAULT(self, user, args):
        raise UnknownHailError()



    def respondTo_gm(self, user, _):
        self.observers.add(user)
        return ('%s is now a GM and will observe private '
                'messages for session %s' % (user, self.channel,))

    
    def respondTo_hello(self, user, _):
        """Greet."""
        return 'Hello %s.' % (user,)

    def respondTo_aliases(self, user, character):
        """Show aliases for a character or for myself"""
        if character is None or character.strip() == '':
            character = user
        formatted = alias.shortFormatAliases(character)
        return 'Aliases for %s:   %s' % (character, formatted)

    def respondTo_unalias(self, user, remove):
        """Remove an alias from a character: unalias [character] <alias>"""
        words = remove.split(None, 1)
        if len(words) > 1:
            key = words[1]
            character = words[0]
        else:
            key = words[0]
            character = user

        removed = alias.removeAlias(key, character)
        if removed is not None:
            return "%s, removed your alias for %s" % (character, key)
        else:
            return "** No alias \"%s\" for %s" % (key, character)

    def respondTo_n(self, user, _):
        """Next initiative"""
        next = self.initiatives.pop(0)
        self.initiatives.append(next)
        if next[1] is None:
            return '++ New round ++'
            # TODO - update timed events here (don't update on prev init)
        else:
            return '%s (init %s) is ready to act . . .' % (next[1], next[0],)

    def respondTo_p(self, user, _):
        """Previous initiative"""
        last, prev = self.initiatives.pop(-1), self.initiatives.pop(-1)
        self.initiatives.append(prev)
        self.initiatives.insert(0, last)
        if prev[1] is None:
            return '++ New round ++'
        else:
            return '%s (init %s) is ready to act . . .' % (prev[1], prev[0],)

    def respondTo_inits(self, user, _):
        """List inits, starting with the currently active character, in order"""
        # the "current" initiative is always at the end of the list
        if len(self.initiatives) > 0:
            current = self.initiatives[-1]
            inits = ['%s/%s' % (current[1], current[0])]
            for init in self.initiatives[:-1]:
                if init[1] is None:
                    name = 'NEW ROUND'
                else:
                    name = init[1]
                inits.append('%s/%s' % (name, init[0]))
            return 'Initiative list: ' + ', '.join(inits)
        else:
            return 'Initiative list: (none)'

    def respondTo_combat(self, user, _):
        """Start combat by resetting initiatives"""
        self.initiatives = [(9999, None)]
        return '** Beginning combat **'

    def respondTo_party(self, user, _):
        if len(self.party.bodies) == 0:
            return '%s, nobody is in the party.' % (user,)
        for char in self.party.bodies:
            FIXME
            return '%(name)s: %(classes)s' % char.summarize()

    def respondTo_iam(self, user, charname):
        """Take control of a character by name."""
        try:
            player = self.club.findExact(user)
        except ValueError:
            player = encounter.Player(user)
            self.club.registerPlayer(player)
        char = self.encounter.find(charname, first=1)
        player.own(char)
        return "%s now owns %s." % (player.getName(), char.getName())

    def respondTo_remove(self, user, charname):
        """Remove a character from an encounter by name."""
        char = self.party.dismiss(charname)
        return "%s is no longer in the party." % (char.getName(),)

    def respondTo_help(self, user, _):
        """This drivel."""
        _commands = []
        commands = []
        for att in dir(self):
            member = getattr(self, att)
            if (att.startswith('respondTo_') 
                and callable(member)
                and att[10:].upper() != att[10:]):  # CAPITALIZED are reserved.
                _commands.append('%s: %s' % (att[10:], member.__doc__))

        _d = {'commands': '\n    '.join(_commands), }

        response = file(fs.help).read() % _d
        return response

    def doInitiative(self, user, result):
        self.initiatives.append((result[0], user))
        self.initiatives.sort()
        self.initiatives.reverse()

    def matchNick(self, nick):
        """True if nick is part of this session."""
        return nick in self.nicks




    def privateInteraction(self, user, msg, parsed):
        return self.doInteraction(user, msg, parsed, user, *self.observers)

    def interaction(self, user, msg, parsed):
        return self.doInteraction(user, msg, parsed, self.channel)

    def doInteraction(self, user, msg, parsed, *recipients):
        """Use actor's stats to apply each action to all targets"""
        if parsed.actor:
            actor = parsed.actor.character_name
        else:
            actor = user

        strings = []
        for vp in parsed.verb_phrases:
            if len(parsed.targets) == 0:
                formatted = alias.resolve(actor, tuple(vp.verbs), vp.dice)
                if formatted is not None:
                    strings.append(formatted)
            else:
                for item in parsed.targets:
                    target = item.target
                    formatted = alias.resolve(actor, tuple(vp.verbs), vp.dice,
                                              target)
                    if formatted is not None:
                        strings.append(formatted)
        if strings:
            text = '\n'.join(strings)
            return Response(text, msg, *recipients)
                



    def command(self, user, command):
        """Choose a method based on the command word, and pass args if any"""
        return self.doCommand(user, command, self.channel)
        
    def privateCommand(self, user, command):
        return self.doCommand(user, command, user, *self.observers)

    def doCommand(self, user, command, *recipients):
        m = self.getCommandMethod(command.command_identifier)

        context = command

        try:
            text = m(user, command.command_args)
            return Response(text, context, *recipients)
        except UnknownHailError, e:
            return Response("wtf?", context, *recipients)
        except Exception, e:
            log.msg(''.join(traceback.format_exception(*sys.exc_info())))
            text = '** Sorry, %s: %s' % (user, str(e)), 
            return Response(text, context, *recipients)
        
    def getCommandMethod(self, command_word):
        return getattr(self, 'respondTo_%s' % (command_word,), 
                       self.respondTo_DEFAULT)

    def addNick(self, *nicks):
        self.nicks |= Set(nicks)
        return self.reportNicks('Added %s' % (str(nicks),))

    def removeNick(self, *nicks):
        self.nicks ^= Set(nicks)
        # also update self.observers
        self.observers ^= Set(nicks)
        return self.reportNicks('Removed %s' % (str(nicks),))

    def reportNicks(self, why):
        nicks = ', '.join(self.nicks)
        return None # FIXME
        return Response("Nicks in this session: %s" % (nicks,), 
                        why,
                        self.channel)

    def rename(self, old, new):
        self.nicks -= Set((old,))
        self.nicks |= Set((new,))
        # also update self.observers
        self.observers -= Set((old,))
        self.observers |= Set((new,))
        if old in self.observers:
            self.observers.remove(old)
            self.observers.append(new)
        # TODO - rename old's aliases so they work for new
        return self.reportNicks('%s renamed to %s' % (old, new))


class Response:
    """A response vector with the channels the response should be sent to"""
    def __init__(self, text, context, channel, *channels):
        self.text = text
        self.context = context
        self.channel = channel
        self.more_channels = channels

    def getMessages(self):
        """Generate messages to each channel"""
        if len(self.more_channels) > 0:
            text = self.text + ' (observed)'
            more_text = '%s (<%s>  %s)' % (self.text, 
                                           self.channel,
                                           self.context)
        else:
            text = self.text

        yield (self.channel, text)
        for ch in self.more_channels:
            yield (ch, more_text)


class VellumTalk(irc.IRCClient):
    """An irc boy that handles D&D game sessions.
    (Currently contains d20-specific assumption about initiative.)
    """
    
    nickname = "VellumTalk"

    def __init__(self, *args, **kwargs):
        self.wtf = 0  # number of times a "wtf" has occurred recently.
        # reset wtf's every 30 seconds 
        self.resetter = task.LoopingCall(self._resetWtfCount).start(30.0)
        self.sessions = []
        self.defaultSession = None
        # TODO - analyze, do i *really* need responding?
        self.responding = 0 # don't start responding until i'm in a channel
        # irc.IRCClient.__init__(self, *args, **kwargs)

    def findSession(self, channel):
        """Return the channel that matches channel, or the channel
        that has channel (a nick) in its list of people
        Otherwise return the defaultSession, usually indicating that someone
        has /msg'd the bot and that person is not in a channel with the bot.
        """
        for session in self.sessions:
            if channel == session.channel:
                return session
            if session.matchNick(channel):
                return session
        return self.defaultSession

    def _resetWtfCount(self):
        self.wtf = 0

    def respondToUnknown(self):
        # we don't want to get caught looping, so respond up to 3 times
        # with wtf, then wait for the counter to reset
        if self.wtf < 3:
            self.wtf = self.wtf + 1
            self.msg("wtf?")
        if self.wtf < 4:
            log.msg("Spam blocking tripped. WTF counter exceeded.")
            self.wtf = self.wtf + 1

    
    def msgSlowly(self, channel, lines, delay=700):
        """Send multiple lines to the channel with delays in the middle
        delay is given in ms
        """
        send = lambda line: self.msg(channel, line)
        send(lines[0])
        for n, line in enumerate(lines[1:]):
            reactor.callLater(n*(delay/1000.0), send, line)

    def sendResponse(self, response):
        if response is None:
            return
        _already = []
        for channel, text in response.getMessages():
            # don't send messages to any users twice
            if channel in _already:
                continue

            splittext = text.splitlines()
            if len(splittext) > 1:
                self.msgSlowly(channel, splittext)
            else:
                self.msg(channel, text)
            _already.append(channel)

    # callbacks for irc events
    # callbacks for irc events
    def connectionMade(self):
        irc.IRCClient.connectionMade(self)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        # create a session to respond to private messages from nicks
        # not in any channel I'm in
        self.defaultSession = Session('')
        linesyntax.setBotName(self.nickname)
        # join my default channel
        self.join(self.factory.channel)

    def joined(self, channel):
        """When the bot joins a channel, find or make a session
        and start tracking who's in the session.
        """
        # find or make a session
        session = self.findSession(channel)
        if session is self.defaultSession: # i.e., not found
            session = Session(channel)
            self.sessions.append(session)

        self.responding = 1

    def left(self, channel):
        session = self.findSession(channel)
        self.sessions.remove(session)

    def kickedFrom(self, channel, kicker, message):
        session = self.findSession(channel)
        self.sessions.remove(session)

    def userJoined(self, user, channel):
        session = self.findSession(channel)
        self.sendResponse(session.addNick(user))

    def userLeft(self, user, channel):
        session = self.findSession(user)
        self.sendResponse(session.removeNick(user))

    def userQuit(self, user, quitmessage):
        session = self.findSession(user)
        self.sendResponse(session.removeNick(user))

    def userKicked(self, user, channel, kicker, kickmessage):
        session = self.findSession(user)
        self.sendResponse(session.removeNick(user))

    def userRenamed(self, old, new):
        session = self.findSession(old)
        self.sendResponse(session.rename(old, new))

    def irc_RPL_NAMREPLY(self, prefix, (user, _, channel, names)):
        nicks = names.split()
        for nick in nicks[:]:
            if nick[0] in '@+':
                nicks.remove(nick)
                nicks.append(nick[1:])

        session = self.findSession(channel)
        self.sendResponse(session.addNick(*nicks))

    def irc_RPL_ENDOFNAMES(self, prefix, params):
        pass

    def irc_unknown(self, prefix, command, params):
        log.msg('|||'.join((prefix, command, repr(params))))

    def irc_INVITE(self, prefix, (user, channel)):
        self.join(channel)

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]
        log.msg(user, channel, msg)
        if not self.responding:
            return
        # Check to see if they're sending me a private message
        # If so, the return channel is the user.
        if channel == self.nickname:
            channel = user

        session = self.findSession(channel)

        parsed = linesyntax.parseSentence(msg)
        if parsed.command:
            if channel == user:
                response = session.privateCommand(user, parsed.command)
            else:
                response = session.command(user, parsed.command)
            self.sendResponse(response)
        elif parsed.verb_phrases:
            if channel == user:
                response = session.privateInteraction(user, msg, parsed)
            else:
                response = session.interaction(user, msg, parsed)
            self.sendResponse(response)
        else:
            pass

    # though it looks weird, actions will behave the same way as privmsgs.
    # for example, /me .hello will behave like "VellumTalk: hello" or ".hello"
    action = privmsg

class VellumTalkFactory(protocol.ClientFactory):
    """A factory for VellumTalks.

    A new protocol instance will be created each time we connect to the server.
    """

    # the class of the protocol to build when new connection is made
    protocol = VellumTalk 

    def __init__(self, channel):
        self.channel = channel

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()


class ResponseTest:
    """Notation for testing a response to a command."""
    def __init__(self, factory, user, channel, sent, *recipients):
        self.user = user
        self.factory = factory
        self.channel = channel
        self.sent = sent

        if len(recipients) == 0:
            self.recipients = None
        else:
            self.recipients = list(recipients)

        self.last_pos = 0

    def check(self):
        pipe = self.factory.pipe
        pipe.seek(self.factory.pipe_pos)
        actual = pipe.read().strip()
        self.factory.pipe_pos = pipe.tell()
        if self.recipients is None:
            if actual == '':
                pass
            else:
                print
                print "(Expected: '')"
                print actual
                return
        else:
            for _line in actual.splitlines():
                for target, expected in self.recipients:
                    pattern = 'PRIVMSG %s :%s' % (re.escape(target), 
                                                  expected)
                    # remove a recipient each time a line is found
                    # matching a line that was expected
                    if re.match(pattern, _line):
                        self.satisfy(target, expected)
                # pass when there are no recipients left to satisfy
                if len(self.recipients) == 0:
                    break
            else:
                print
                for target, expected in self.recipients:
                    print ' '*10 + ' '*len(target) + expected
                print actual
                return
        return 1

    def satisfy(self, target, expected):
        self.recipients.remove((target, expected))

class ResponseTestFactory:
    def __init__(self, pipe):
        self.pipe = pipe
        self.pipe_pos = 0
    def next(self, user, channel, target, *recipients):
        return ResponseTest(self,
                            user,
                            channel, 
                            target, 
                            *recipients)

passed = 0
def succeed():
    global passed
    passed = passed + 1
    sys.stdout.write('.')

from twisted.words.test.test_irc import StringIOWithoutClosing
pipe = StringIOWithoutClosing()
factory = ResponseTestFactory(pipe)
GeeEm = (lambda channel, target, *recipients: 
            factory.next('GeeEm', channel, target, *recipients))
Player = (lambda channel, target, *recipients: 
            factory.next('Player', channel, target, *recipients))

testcommands = [
GeeEm('VellumTalk', 'hello',),
GeeEm('VellumTalk', 'VellumTalk: hello', ('GeeEm', r'Hello GeeEm\.')),
GeeEm('VellumTalk', 'Vellumtalk: hello there', ('GeeEm', r'Hello GeeEm\.')),
GeeEm('VellumTalk', '.hello', ('GeeEm', r'Hello GeeEm\.')),
GeeEm('#testing', 'hello',),
GeeEm('#testing', 'VellumTalk: hello', ('#testing', r'Hello GeeEm\.')),
GeeEm('#testing', '.hello', ('#testing', r'Hello GeeEm\.')),
GeeEm('VellumTalk', '.inits', ('GeeEm', r'Initiative list: \(none\)')),
GeeEm('VellumTalk', '.combat', ('GeeEm', r'\*\* Beginning combat \*\*')),
GeeEm('#testing', '[init 20]', ('#testing', r'GeeEm, you rolled: init 20 = \[20\]')),
GeeEm('VellumTalk', '.n', ('GeeEm', r'\+\+ New round \+\+')),
GeeEm('VellumTalk', '.n', ('GeeEm', r'GeeEm \(init 20\) is ready to act \. \. \.')),
GeeEm('VellumTalk', '.p', ('GeeEm', r'\+\+ New round \+\+')),
GeeEm('VellumTalk', '.p', ('GeeEm', r'GeeEm \(init 20\) is ready to act \. \. \.')),
GeeEm('VellumTalk', '.inits', ('GeeEm', r'Initiative list: GeeEm/20, NEW ROUND/9999')),
# GeeEm('VellumTalk', 'help', ('GeeEm', r'\s+hello: Greet\.')), FIXME
GeeEm('VellumTalk', '.aliases', ('GeeEm', r'Aliases for GeeEm:   init=20')),
GeeEm('VellumTalk', '.aliases GeeEm', ('GeeEm', r'Aliases for GeeEm:   init=20')),
GeeEm('VellumTalk', '.unalias foobar', ('GeeEm', r'\*\* No alias "foobar" for GeeEm')),
GeeEm('#testing',  'hello [argh 20] [foobar 30]', ('#testing', r'GeeEm, you rolled: argh 20 = \[20\]')),
GeeEm('VellumTalk', '.unalias init', ('GeeEm', r'GeeEm, removed your alias for init')),
GeeEm('VellumTalk', '.aliases', ('GeeEm', r'Aliases for GeeEm:   argh=20, foobar=30')),
]

testhijack = [
GeeEm('VellumTalk', '*grimlock1 does a [smackdown 1000]', ('GeeEm', 'grimlock1, you rolled: smackdown 1000 = \[1000\]')),
GeeEm('#testing', '*grimlock1 does a [bitchslap 1000]', ('#testing', 'grimlock1, you rolled: bitchslap 1000 = \[1000\]')),
GeeEm('VellumTalk', '*grimlock1 does a [smackdown]', ('GeeEm', 'grimlock1, you rolled: smackdown = \[1000\]')),
GeeEm('VellumTalk', 'I do a [smackdown]'),
GeeEm('VellumTalk', '.aliases grimlock1', ('GeeEm', 'Aliases for grimlock1:   bitchslap=1000, smackdown=1000')),
GeeEm('VellumTalk', '.unalias grimlock1 smackdown', ('GeeEm', 'grimlock1, removed your alias for smackdown')),
GeeEm('VellumTalk', '.aliases grimlock1', ('GeeEm', 'Aliases for grimlock1:   bitchslap=1000')),
]

testobserved = [
GeeEm('VellumTalk', '.gm', ('GeeEm', r'GeeEm is now a GM and will observe private messages for session #testing')),
Player('VellumTalk', '[stabtastic 20]', 
   ('GeeEm', r'Player, you rolled: stabtastic 20 = \[20\] \(<Player>  \[stabtastic 20\]\)'),
   ('Player', r'Player, you rolled: stabtastic 20 = \[20\] \(observed\)')
   )
]

testobserved2 = [
Player('VellumTalk', '[stabtastic 20]', 
   ('Player', r'Player, you rolled: stabtastic 20 = \[20\]$')
   )
]
# TODO - move d20-specific tests, e.g. init and other alias hooks?

def test():
    # save off and clear alias.aliases, since it gets persisted # FIXME
    orig_aliases = alias.aliases
    alias.aliases = {}
    try:
        transport = protocol.FileWrapper(pipe)
        vt = VellumTalk()
        vt.performLogin = 0
        vt.joined("#testing")
        vt.defaultSession = Session('#testing')
        vt.makeConnection(transport)
        linesyntax.setBotName('VellumTalk')

        testOneSet(testcommands, vt)
        testOneSet(testhijack, vt)
        testOneSet(testobserved, vt)

        vt.userLeft('GeeEm', '#testing')
        testOneSet(testobserved2, vt)
    finally:
        # restore original aliases when done, so save works
        alias.aliases = orig_aliases
        global passed
        print passed
        passed = 0

def testOneSet(test_list, vt):
    for r in test_list:
        vt.privmsg(r.user, r.channel, r.sent)
        if r.check():
            succeed()

