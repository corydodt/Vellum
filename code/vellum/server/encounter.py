"""
Management for encounters.  Keep track of who's involved, who can be
a target, who controls what, etc.
"""

from zope.interface import implements, Interface

import yaml

class INamedThing(Interface):
    """A thing with a name property which is a string."""
    def getName(self):
        """Return the name string."""


def matchByName(name, targets):
    matches = []
    name = name.lower()
    for candidate in targets:
        possible = INamedThing(candidate).getName().lower()
        pos = possible.find(name)
        if pos >= 0:
            matches.append((pos, candidate))
    if len(matches) > 0:
        matches.sort()
        return zip(*matches)[1]
    else:
        return matches

class Directory:
    """Searchable group of named bodies"""
    def __init__(self):
        self.bodies = []
    def find(self, name, onlyone=0, first=0):
        """Find a player by name.
        onlyone means fail if there's multiple matches.
        first means return only the first match, even if there
        are multiple.
        """
        matches = matchByName(name, self.bodies)
        if not onlyone and not first:
            return matches
        else:
            if len(matches) == 1:
                return matches[0]
            elif len(matches) == 0:
                raise ValueError("None of %s found." % (name,))
            else:
                if first:
                    return matches[0]
                raise ValueError("More than one %s found." % (name,))
    def findExact(self, name):
        for body in self.bodies:
            if body.name == name:
                return body
        raise ValueError("None of %s found." % (name,))


class Club(Directory):
    """
    All the players.
    """
    def registerPlayer(self, player):
        self.bodies.append(player)

class Player:
    """
    Control panel for the person at the keyboard.
    """
    implements(INamedThing)

    def __init__(self, name):
        self.owned = []
        self.name = name

    def own(self, char):
        self.owned.append(char)

    def disown(self, char):
        self.owned.remove(char)

    def getName(self):
        return self.name

class Encounter(Directory):
    """A bunch of characters with relationships."""
    def addCharacter(self, character):
        self.bodies.append(character)


    def dismiss(self, name):
        """Dismiss a character from the encounter."""
        char = self.find(name, onlyone=1)
        self.bodies.remove(char)
        return char

    def save(self):
        TODO



class Character:
    """Rudimentary character.  Has behavior."""
    implements(INamedThing)

    def __init__(self, filename=None):
        self.weapons = []
        self.behavior = None
        if filename is not None:
            data = yaml.loadFile(filename).next()
            self.__dict__.update(data)
            self.behavior = CharacterBehavior(data)
            for weapon in self.weapons:
                self.behavior.learn("FIXME") # FIXME


    def summarize(self):
        return dict(name=self.name, classes=self.classes)
    def getName(self):
        return self.name

    def save(self):
        TODO

class CharacterBehavior:
    """
    The set of things that can be done by the person controlling the
    character, using the bot as an agent.
    Aliases, for example.
    """
    def __init__(self, data):
        actions = []

    def learn(self, syntax, args=None):
        """Learn a new action.  Syntax is how it can be invoked.
        args is the list of argument names, so arguments can be passed in.
        """
