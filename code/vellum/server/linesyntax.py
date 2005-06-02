r"""Define the syntax for parsing statements on IRC.
Lines may contain the following syntax:
    - A message that begins with the bot's name or begins with a dot
      is a structured command (beginning on the first token after the bot's
      name, if present), and it may take arguments.
    - A single word beginning with a letter and prefixed by a * anywhere in
      the line is the name of an NPC or a PC.
    - An expression inside brackets [] is a verb.
    - A verb starts with zero or more verbnames, and ends with an optional dice
      expression.
    - A dice expression: all of the following are valid..
        5    5x3    5+1x3    d6    3d6     d6+2     9d6l3-1x2    3d6x6sort
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


L = P.Literal
CL = P.CaselessLiteral
Sup = P.Suppress


# commands
# commands
# commands
botname = P.Forward()

def setBotName(newname):
    botname << CL(newname)


identifier = P.Word(P.alphas+"_", P.alphanums+"_").setResultsName('identifier')
command_leader = L(".")
hail = (botname + P.oneOf(": ,")) | (botname + P.White())
command_args = P.restOfLine.setResultsName('command_args')


command = (P.StringStart() + 
           Sup(command_leader | hail) + 
           identifier.setResultsName('command_identifier') + 
           Sup(P.Optional(P.White())) +
           command_args.setResultsName('command_args')).setResultsName('command')

_test_commands = [(".hello", "['hello', '']"),
(".foo bar", "['foo', 'bar']"),
(". foo", "['foo', '']"),
("..foo", P.ParseException),
("TestBot:foo", "['foo', '']"),
("tesTBot,foo", "['foo', '']"),
("TestBot foo", "['foo', '']"),
("TestBot: foo", "['foo', '']"),
("tesTBot, foo", "['foo', '']"),
("tesTBotfoo", P.ParseException),
]

# interactions
# interactions
# interactions

# actor
character_name = P.Word(P.alphas, P.alphanums+"_").setResultsName('character_name')

actor = (Sup('*') + character_name).setResultsName('actor')


# dice expressions
# general format:
#
#    number ::== {'0'-'9'}...
#    filter ::= { 'h' | 'l' } number
#    bonus ::=  { '+' | '-'} number
#    repeat ::= 'x' number
#    size ::== 'd' number
#    random ::= [ number ] size [ filter ] [ bonus ] [ repeat ]
#    nonrandom ::= number [ bonus ] [ repeat ]
#    
number = P.Word(P.nums)
number.setParseAction(lambda s,p,t: map(int, t))

dice_count = number.setResultsName('dice_count')
dice_size = Sup(CL('d')) + number.setResultsName('dice_size')
dice_bonus = P.oneOf('+ -') + number.setResultsName('dice_bonus')
dice_filter = (P.oneOf('h l', caseless=True).setResultsName('dice_hilo') +
               number.setResultsName('dice_filter'))
dice_sorted = CL('sort').setResultsName('dice_sorted')
dice_repeat = (Sup(CL('x')) + 
               number.setResultsName('dice_repeat') + 
               P.Optional(dice_sorted))

def combineBonus(sign, num):
    values = {'-':-1, '+':1}
    return num * values[sign]

class FilterException(Exception):
    """Filter has more dice than the dice_count"""

dice_bonus.setParseAction(lambda s, p, t: combineBonus(*t))
dice_bonus = dice_bonus.setResultsName('dice_bonus')

dice_optionals = P.Optional(dice_bonus) + P.Optional(dice_repeat)

nonrandom = dice_count + dice_optionals
random = (P.Optional(dice_count, default=1) + 
          dice_size +
          P.Optional(dice_filter) + 
          dice_optionals)

dice = (random | nonrandom).setResultsName('dice')
dice_string = dice + P.StringEnd()

_test_dice = [("5", "[5]"),
("5x3","[5, 3]"),
("5+1x3","[5, 1, 3]"),
("d6x3","[1, 6, 3]"),
("1d20+1","[1, 20, 1]"),
("9d6l3-10x2","[9, 6, 'l', 3, -10, 2]"),
("9d6H3+10x2","[9, 6, 'h', 3, 10, 2]"),
("1d  6 X3","[1, 6, 3]"),
("d 6 -2 x 3","[1, 6, -2, 3]"),
("2d6-2x1","[2, 6, -2, 1]"),
("2d6-2x2sort","[2, 6, -2, 2, 'sort']"),
("2d6sort", P.ParseException),
("d6xz", P.ParseException),
("1d", P.ParseException),
("1d6l3l3", P.ParseException),
("1d6h3l3", P.ParseException),
("d6h+1", P.ParseException),
]

# temporary modifier
# temporary modifier
temp_modifier = dice_bonus.setResultsName('temp_modifier')

# verb phrases
# verb phrases
o = L('[')
t = L(']')
wordchars = P.alphanums + string.punctuation.replace(']', '')

v_word = P.Word(wordchars)
v_words = P.OneOrMore(v_word).setResultsName('verbs')

v_word_nonterminal = v_word + P.NotAny(t)
v_words_nonterminal = P.OneOrMore(v_word_nonterminal).setResultsName('verbs')

# FIXME - [d20 1d10] should be an error
v_content = P.Optional(v_words_nonterminal) + (temp_modifier | dice) | v_words
verb_phrase = Sup(o) + v_content + Sup(t)
verb_phrase = verb_phrase.setResultsName('verb_phrase')

_test_verb_phrases = [
("[]", P.ParseException),
("[star]", "['star']"),
("[rock star]", "['rock', 'star']"),
("[woo 1d20+1]", "['woo', 1, 20, 1]"),
("[woo +2]", "['woo', 2]"),
("[woo -2]", "['woo', -2]"),
("[1d20+1]", "[1, 20, 1]"),
("[1d20+1 1d20+1]", "['1d20+1', 1, 20, 1]"),
("[arrr matey 1d20+1x7sort]", "['arrr', 'matey', 1, 20, 1, 7, 'sort']"),
("[i am a star", P.ParseException),
]


# targets
# targets
target_leader = L('@')
target = (Sup(target_leader) + character_name).setResultsName('target')

_test_targets = [
("@a", "['a']"),
("@ a", "['a']"),
("@@", P.ParseException),
("@123", P.ParseException),
]


# bring it all together
# bring it all together

# sentence
# sentence
# sentence
sentence = command | verb_phrase | actor | target

_test_sentences = [
(".gm", "['gm', '']"),
(".combat", "['combat', '']"),
("lalala", "[]"),
("TestBot, n", "['n', '']"),
("testbot: n", "['n', '']"),
("testbot n", "['n', '']"),
("The [machinegun] being fired at @Shara by the *ninja goes rat-a-tat.",
        "['ninja', ['machinegun'], 'Shara']"),
("*woop1", "[]"), # verb phrases are required
("[foo] *woop2", "['woop2', ['foo']]"),
(".aliases shara", "['aliases', 'shara']"),
(".foobly doobly doo", "['foobly', 'doobly doo']"),
("*grimlock1 [attack 1d2+10]s the paladin. (@shara)", 
        "['grimlock1', ['attack', 1, 2, 10], 'shara']"),
("I [attack 1d6+1] @grimlock1", "[['attack', 1, 6, 1], 'grimlock1']"),
("I [attack -1] @grimlock1", "[['attack', -1], 'grimlock1']"), # temp mod
("I [attack +1] @grimlock1", "[['attack', 1], 'grimlock1']"), # temp mod
("I [attack 1d6+1x2sort] @grimlock1", "[['attack', 1, 6, 1, 2, 'sort'], 'grimlock1']"),
("I [cast] a [fireball] @grimlock1 and @grimlock2", 
        "[['cast'], ['fireball'], 'grimlock1', 'grimlock2']"),
("I [cast] a [fireball] @grimlock1 and@grimlock2", 
        "[['cast'], ['fireball'], 'grimlock1', 'grimlock2']"),
]

_test_sentences_altbot = [
("VellumTalk: combat", "['combat', '']"),
("vELLUMTAlk aliases shara", "['aliases', 'shara']"),
]

# convert scanned sentences into a normalized form and then parse them
verb_phrases = P.OneOrMore(P.Group(verb_phrase)).setResultsName('verb_phrases')
targets = P.OneOrMore(target).setResultsName('targets')
normalized_sentence = (command | 
                       P.Optional(actor) + verb_phrases + P.Optional(targets) | 
                       Sup(P.Empty()))

def parseSentence(s):
    actor = None
    verb_phrases = []
    targets = []
    for item, _, _ in sentence.scanString(s):
        if item.command:
            return item
        elif item.actor:
            actor = item.actor.character_name
        elif item.verb_phrase:
            verb_phrases.append(item.verb_phrase)
        elif item.target:
            targets.append(item.target.character_name)

    normalized = formatNormalized(actor, verb_phrases, targets)
    parsed = normalized_sentence.parseString(normalized)
    return parsed

def formatNormalized(actor, verb_phrases, targets):
    """Return a string with only the parts of speech, so a parseString
    ParseResults object can be return instead of a scanString result.
    """
    _fm_verb_phrases = []
    for vp in verb_phrases:
        verb_list = ' '.join(vp.verbs)
        if vp.dice:
            dice_expr = reverseFormatDice(vp.dice)
        elif vp.temp_modifier:
            dice_expr = '%+d' % (vp.temp_modifier,)
        else:
            dice_expr = ''

        verb_body = ' '.join((verb_list, dice_expr))
        _fm_verb_phrases.append('[%s]' % (verb_body,))
    fm_verb_phrases = ' '.join(_fm_verb_phrases)

    _fm_targets = []
    for targ in targets:
        _fm_targets.append('@%s' % (targ,))
    fm_targets = ' '.join(_fm_targets)

    if actor is not None:
        _actor = '*%s ' % (actor,)
    else:
        _actor = ''


    return '%s%s %s' % (_actor, fm_verb_phrases, fm_targets)

def reverseFormatDice(parsed_dice):
    """Take a parsed dice expression and return the string form"""
    _dice_expr = []
    if parsed_dice.dice_count:
        _dice_expr.append(str(parsed_dice.dice_count))
    if parsed_dice.dice_size:
        _dice_expr.append('d' + str(parsed_dice.dice_size))
    if parsed_dice.dice_hilo:
        _dice_expr.append(str(parsed_dice.dice_hilo[0]))
    if parsed_dice.dice_filter:
        _dice_expr.append(str(parsed_dice.dice_filter))
    if parsed_dice.dice_bonus:
        _dice_expr.append('%+d' % (parsed_dice.dice_bonus,))
    if parsed_dice.dice_repeat:
        _dice_expr.append('x' + str(parsed_dice.dice_repeat))
    if parsed_dice.dice_sorted:
        _dice_expr.append('sort')
    return ''.join(_dice_expr)



def testStuff(method, tests):
    for input, expected in tests:
        try:
            parsed = method(input)
            if isinstance(expected, basestring):
                if str(parsed) != expected:
                    print '\n', input, 'Wanted', expected, 'Got', str(parsed)
                else:
                    passed()
            else:
                print "\nFAILED:", input, 'Wanted', expected, 'Got', parsed
        except Exception, e:
            if isinstance(expected, basestring):
                print "\nFAILED:", input, expected
                raise
            if not isinstance(e, expected):
                print input, expected, str(parsed)
            else:
                passed()

passcount = 0

def passed():
    global passcount
    passcount = passcount + 1
    sys.stdout.write('.')


def test():
    setBotName('TestBot')
    testStuff(command.parseString, _test_commands)
    testStuff(dice_string.parseString, _test_dice)
    testStuff(verb_phrase.parseString, _test_verb_phrases)
    testStuff(target.parseString, _test_targets)

    testStuff(parseSentence, _test_sentences)
    setBotName('VellumTalk')
    testStuff(parseSentence, _test_sentences_altbot)

    print passcount

if __name__ == '__main__':
    test()
