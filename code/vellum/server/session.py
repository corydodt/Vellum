import sys
import traceback
from sets import Set

from twisted.python import log

from vellum.server import gametime, alias
from vellum.server.fs import fs


class UnknownHailError(Exception):
    pass

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

class Session:
    def __init__(self, channel):
        self.channel = channel
        # TODO - move this into d20-specific code somewhere
        self.initiatives = []
        self.nicks = Set() # TODO - add a wrapper function for fixing bindings
                           # when nicks are removed or added
        self.observers = Set()
        self.clock = gametime.Clock()
        # TODO - deserialize clock

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
        self.initiatives.append((result[0].sum(), user))
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
                formatted = alias.resolve(actor,
                                          tuple(vp.verbs),
                                          vp.dice,
                                          vp.temp_modifier)
                if formatted is not None:
                    strings.append(formatted)
            else:
                for item in parsed.targets:
                    target = item.target
                    formatted = alias.resolve(actor,
                                              tuple(vp.verbs),
                                              vp.dice,
                                              vp.temp_modifier,
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
        return None # FIXME - very spammy when on
        return Response("Nicks in this session: %s" % (nicks,),
                        why,
                        self.channel)

    def rename(self, old, new):
        self.nicks -= Set((old,))
        self.nicks |= Set((new,))
        # also update self.observers
        if old in self.observers:
            self.observers -= Set((old,))
            self.observers |= Set((new,))
        # TODO - rename old's aliases so they work for new
        return self.reportNicks('%s renamed to %s' % (old, new))

