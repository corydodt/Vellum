r"""Define the syntax for parsing statements on IRC.
Lines beginning with . are commands, unless the next significant character is
a dot as well.
Lines that are not commands may contain the following syntax:
    - A message that begins with the bot's name or begins with a dot
      is a structured command (beginning on the first token after the bot's
      name, if present), and it may take arguments.
    - A single word beginning with a letter and prefixed by a * anywhere in
      the line is the name of an NPC or a PC.
    - An expression inside brackets [] or braces {} is a verb.
    - A verb starts with zero or more verbnames, and ends with an optional dice
      expression.
    - A dice expression: all of the following are valid..
        5    5x3    5+1x3    d6    3d6     9d6l3-1x2    d6+2
    - A targetting expression starts with "vs" or "vs." and is followed by a
      comma-separated list of character names
"""

try:
    pass
    # import psyco # TODO - see how much of a difference this makes
    # psyco.profile()
except ImportError:
    pass

import sys
import string

import pyparsing as P

class BotName(P.CaselessLiteral):
    """Token to caseless match the botname, whatever it happens to be now."""
    def setBotName(self, matchString):
        self.__init__(matchString)

botname = BotName('BOTNAME_NOT_SET')



def R(name):
    """A testy function that just reports the name of the thing parsed
    along with the tokens found
    """
    def reporter(s, loc, toks):
        pass # print "%20s %-50s" % (name, toks)
    return reporter

L = P.Literal
Sup = P.Suppress


# commands
# commands
# commands
identifier = P.Word(P.alphas+"_", P.alphanums+"_")
command_leader = L(".")
hail = botname + P.Optional(L(":") | L(","))


command = (P.StringStart() + 
           Sup(command_leader | hail) + 
           identifier + 
           P.restOfLine)

_test_commands = [(".hello", "['hello', '']"),
(".foo bar", "['foo', ' bar']"),
(". foo", "['foo', '']"),
("..foo", P.ParseException),
("TestBot foo", "['foo', '']"),
("TestBot: foo", "['foo', '']"),
("tesTBot, foo", "['foo', '']"),
("tesTBotfoo", P.ParseException),
]

# interactions
# interactions
# interactions

# actor
character_name = P.Word(P.alphas, P.alphanums+"_")

actor = Sup('*') + character_name 
actor.setParseAction(R("actor"))


# dice expressions
number = P.Word(P.nums)
number.setParseAction(lambda s,p,t: map(int, t))

dice_count = number.copy()
dice_size = Sup(L('d')) + number
dice_modifier = P.oneOf('+ -') + number
dice_filter = P.oneOf('h l', caseless=True) + number
dice_repeat = Sup(P.CaselessLiteral('x')) + number

def combineModifier(sign, num):
    values = {'-':-1, '+':1}
    return num * values[sign]

class FilterException(Exception):
    """Filter has more dice than the dice_count"""

dice_modifier.setParseAction(lambda s, p, t: combineModifier(*t))

dice_optionals = (P.Optional(dice_filter) +
                  P.Optional(dice_modifier) + 
                  P.Optional(dice_repeat))

nonrandom = dice_count + dice_optionals
random = P.Optional(dice_count) + dice_size + dice_optionals

dice = random | nonrandom 

_test_dice = [("5", "[5]"),
("5x3","[5, 3]"),
("5+1x3","[5, 1, 3]"),
("d6x3","[6, 3]"),
("1d20+1","[1, 20, 1]"),
("9d6l3-10x2","[9, 6, 'l', 3, -10, 2]"),
("9d6H3+10x2","[9, 6, 'h', 3, 10, 2]"),
("1d  6 X3","[1, 6, 3]"),
("d 6 -2 x 3","[6, -2, 3]"),
("2d6-2x1","[2, 6, -2, 1]"),
("d6xz", P.ParseException),
("1d", P.ParseException),
("1d6l3l3", P.ParseException),
("1d6h3l3", P.ParseException),
("d6h+1", P.ParseException),
("1d6h2+1", FilterException),
]


# verb phrases
# verb phrases
def _bookendedVerb(opener, terminator):
    o = L(opener)
    t = L(terminator)
    wordchars = P.alphanums + string.punctuation.replace(terminator, '')

    v_word = P.Word(wordchars)
    v_words = P.OneOrMore(v_word)
    
    v_word_nonterminal = v_word + P.NotAny(t)
    v_words_nonterminal = P.OneOrMore(v_word_nonterminal)

    # FIXME - [d20 1d10] should be an error
    v_content = P.Optional(v_words_nonterminal) + dice | v_words
    v_phrase = Sup(o) + v_content + Sup(t)
    return v_phrase

unsorted_v_phrase = _bookendedVerb('[', ']')
sorted_v_phrase = _bookendedVerb('{', '}')

verb_phrase = sorted_v_phrase | unsorted_v_phrase

_test_verb_phrases = [
("[]", P.ParseException),
("[star]", "['star']"),
("[rock star]", "['rock', 'star']"),
("[woo 1d20+1]", "['woo', 1, 20, 1]"),
("[1d20+1]", "[1, 20, 1]"),
("[1d20+1 1d20+1]", "['1d20+1', 1, 20, 1]"),
("{1d20+1}", "[1, 20, 1]"),
("{arrr matey 1d20+1}", "['arrr', 'matey', 1, 20, 1]"),
("{arrr matey}", "['arrr', 'matey']"),
("[i am a star}", P.ParseException),
]


# targets
# targets
vs = P.CaselessLiteral('vs') + P.Optional(L('.')) 
character_list = P.delimitedList(character_name, ",")
target_phrase = Sup(vs) + character_list

_test_target_phrases = [
("vs. a", "['a']"),
("vs a", "['a']"),
("vs. a, b", "['a', 'b']"),
("vs a, b", "['a', 'b']"),
("Vs a, b, c", "['a', 'b', 'c']"),
("vs . ninja", P.ParseException),
("vs foo, @", P.ParseException),
("vsfoo", P.ParseException),
]


# bring it all together
# bring it all together
part_of_speech = verb_phrase | actor | target_phrase
part_of_speech.setParseAction(R("part_of_speech"))



# sentence
# sentence
# sentence
sentence = command | part_of_speech

_test_sentences = [
(".gm", "['gm', '']"),
(".combat", "['combat', '']"),
("lalala", "[]"),
("TestBot, n", "['n', '']"),
("testbot: n", "['n', '']"),
("testbot n", "['n', '']"),
("The [machinegun] being fired vs. Shara by the *ninja goes rat-a-tat.",
        "['machinegun', 'Shara', 'ninja']"),
("*woop1", "['woop1']"),
("foo *woop2", "['woop2']"),
(".aliases shara", "['aliases', ' shara']"),
(".foobly doobly doo", "['foobly', ' doobly doo']"),
("*grimlock1 [attack 1d2+10]s the paladin. (vs shara)", 
        "['grimlock1', 'attack', 1, 2, 10, 'shara']"),
("I [attack 1d6+1] vs grimlock1", "['attack', 1, 6, 1, 'grimlock1']"),
("I [cast] a [fireball] vs grimlock1,grimlock2", 
        "['cast', 'fireball', 'grimlock1', 'grimlock2']"),
("I [cast] a [fireball] vs grimlock1, grimlock2", 
        "['cast', 'fireball', 'grimlock1', 'grimlock2']"),
]

_test_sentences_altbot = [
("VellumTalk: combat", "['combat', '']"),
("vELLUMTAlk aliases shara", "['aliases', ' shara']"),
]





def test_stuff(element, tests, scanning=False):
    for input, expected in tests:
        try:
            parsed = []
            if scanning:
                scanned = list(element.scanString(input))
                # import pdb; pdb.set_trace()
                for s in scanned:
                    parsed.extend(s[0])
            else:
                parsed = element.parseString(input)
            if isinstance(expected, basestring):
                if str(parsed) != expected:
                    print '\n', input, expected, str(parsed)
                else:
                    passed()
        except Exception, e:
            if isinstance(expected, basestring):
                print "\nFAILED:", input, expected
                raise
            if not isinstance(e, expected):
                print input, expected, str(parsed)
            else:
                passed()

import itertools
passcount = itertools.count()
passcount.next()

def passed():
    passcount.next()
    sys.stdout.write('.')


def test():
    botname.setBotName("TestBot")

    test_stuff(command, _test_commands)
    test_stuff(dice, _test_dice)
    test_stuff(verb_phrase, _test_verb_phrases)
    test_stuff(target_phrase, _test_target_phrases)

    test_stuff(sentence, _test_sentences, scanning=True)
    botname.setBotName('VellumTalk')
    test_stuff(sentence, _test_sentences_altbot, scanning=True)

    print passcount.next() - 1

if __name__ == '__main__':
    test()
