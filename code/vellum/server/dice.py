import sys
import random

from vellum.server import linesyntax
import pyparsing

def rollDie(die, mod=0):
    return random.choice(range(1, die+1)) + mod

def parseRange(odds):
    if '-' in odds:
        low,hi = odds.split('-')
    else:
        low = hi = odds
    return int(low), int(hi)

def choosePercentile(percentiles):
    """Utility function for choosing an item from a list formatted like this:
    ['01-11','13-73','74-99','100']
    Returns the index of the item selected from the list.
    """
    pctile = roll(100)
    for n, outcome in enumerate(percentiles):
        low,hi = parseRange(outcome)
        if low <= pctile <= hi:
            return n
    raise RuntimeError, "None of %s were selected" % (percentiles,)


def parse(st):
    parsed = linesyntax.dice_string.parseString(st)
    rolled = roll(parsed)
    return list(rolled)

def roll(parsed):
    # set these to defaults in the finish step, not in the init, 
    # so the parser instance can be reused
    if parsed.dice_count:
        dice_count = parsed.dice_count
    else:
        dice_count = 1
    if parsed.dice_filter:
        dice_filter_count = int(parsed.dice_filter)
        if dice_filter_count > dice_count:
            _m = "Hi/Lo filter uses more dice than are being rolled"
            raise RuntimeError(_m)

        hilo = str(parsed.dice_hilo[0])
    else:
        dice_filter_count = 0
        hilo = None

    if parsed.dice_repeat:
        dice_repeat = parsed.dice_repeat
    else:
        dice_repeat = 1
    if parsed.dice_bonus:
        dice_bonus = parsed.dice_bonus
    else:
        dice_bonus = 0
    if parsed.dice_size == '':
        # an int by itself is just an int.
        if not parsed.dice_size:
            for n in xrange(dice_repeat):
                yield DiceResult([parsed.dice_count], dice_bonus)
            return
        raise RuntimeError("Syntax error: No die size was given")
    for n in xrange(dice_repeat):
        dierolls = []
        for n in xrange(dice_count):
            dierolls.append(rollDie(parsed.dice_size, 0))
        result = DiceResult(dierolls, dice_bonus, hilo, dice_filter_count)
        yield result

class DiceResult:
    """Representation of all the values rolled by a dice expression."""
    def __init__(self, dierolls, bonus, filterdirection=None, filtercount=0):
        self.dierolls = dierolls
        self.bonus = bonus
        self.filterdirection = filterdirection
        self.filtercount = filtercount

    def __repr__(self):
        return 'DiceResult(=%s)' % self.sum()

    def format(self):
        """Print the sum of the individual (filtered) dice and bonus"""
        dierolls = self.filtered()[:]
        if self.bonus:
            dierolls.append(self.bonus)

        if len(dierolls) > 1:
            formatted_sum = '+'.join(map(str, dierolls))
            return '%s = %s' % (formatted_sum, self.sum())
        else:
            return str(self.sum())

    def filtered(self):
        if self.filterdirection is None:
            filter = lambda: self.dierolls
        elif self.filterdirection in 'hH':
            filter = self.most
        elif self.filterdirection in 'lL':
            filter = self.least
        return filter()

    def sum(self):
        return sum(self.filtered()) + self.bonus

    def __cmp__(self, other):
        return cmp(self.sum(), other.sum())

    def most(self, direction=1):
        """Return the greatest <count> items in lst"""
        lst = self.dierolls[:]
        lst.sort()
        if direction == 1:
            lst.reverse()
        return lst[:self.filtercount]

    def least(self):
        return self.most(0)


def test():
    for dice in ['d6xz',  # repeat not a number
                 '1d', # left out die size 
                 '1d6l3l3', '1d6h3l3',  # can't specify more than one filter
                 '1d6h+1', # can't leave the die count out of the filter
                 '1d6h2+1', # can't keep more dice than you started with
                 '', # empty should be an error
                 '1d6+5 1d1', # multiple expressions
                 ]:
        try:
            parse(dice)
        except (pyparsing.ParseException, RuntimeError), e:
            print e
        else:
            assert 0, "%s did not cause an error, and should've" % (dice,)
    print parse('5')
    print parse('5x3')
    print parse('5+1x3')
    print parse('d6x3')
    print parse('9d6l3-10x2')
    print parse('9d6H3+10x2')
    print parse('1d  6 x3')
    print parse('d 6 -2 x 3')
    print parse('2d6-2x1')
    for n in xrange(1000):
        assert parse('5')[0].sum() == 5
        assert parse('5x3')[2].sum() == 5
        assert parse('5+1x3')[2].sum() == 6
        assert 1 <= parse('d6')[0].sum() <= 6
        assert 3 <= parse('3d6')[0].sum() <= 18
        assert 1 <= parse('1d  6')[0].sum() <= 6
        assert 3 <= parse('d6+2')[0].sum() <= 8
        assert -1 <= parse('d 6 -2')[0].sum() <= 4
        assert 4 <= parse('2d6+ 2')[0].sum() <= 14
        assert 0 <= parse('2d6-2')[0].sum() <= 10
        assert 4 <= parse('9d6h3+1x2')[0].sum() <= 19
        assert 2 <= parse('9d6L3-1x2')[0].sum() <= 17
    print 'passed all tests'

def run(argv=None):
    import linesyntax
    if argv is None:
        argv = sys.argv
    while 1:
        try:
            st = raw_input("Roll: ")
            rolled = parse(st)
            if len(list(rolled)) > 1:
                print "Unsorted--", rolled
                rolled.sort()
                rolled.reverse()
                print "Sorted----", rolled
            else:
                print rolled[0]
        except RuntimeError, e:
            print e

if __name__ == '__main__':
    sys.exit(run())
