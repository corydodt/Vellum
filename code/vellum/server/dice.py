import sys
import random
import sre

def roll(die, mod=0):
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


def most(lst, count, direction=1):
    """Return the greatest <count> items in lst"""
    lst.sort()
    if direction == 1:
        lst.reverse()
    return lst[:count]

least = lambda l, c: most(l, c, -1)

class Roller:
    def __init__(self):
        self.repeat = self.count = self.dice = self.modifier = 0
        self.filter = None
        self.scanner = sre.Scanner([
                (r'\s+', self.got_nothin),
                (r'd\s*[0-9]+', self.got_dice),
                (r'[0-9]+', self.got_count),
                (r'[lLhH]\s*[0-9]+', self.got_filter),
                (r'(\+|\-)\s*[0-9]+', self.got_modifier),
                (r'[Xx]\s*[0-9]+', self.got_repeat),
                (r'.*', self.got_unknown),
                ])

    def got_unknown(self, scanner, token):
        last = self.last
        self.reset()
        raise RuntimeError("Syntax error: %s" % (last,))
    def got_nothin(self, scanner, token): pass
    def got_dice(self, scanner, token):
        self.dice = int(token[1:])
    def got_count(self, scanner, token):
        self.count = int(token)
    def got_filter(self, scanner, token):
        key = token[0]
        num = int(token[1:])
        if self.filter is not None:
            s = "Syntax error: Multiple filters specified in %s"
            raise RuntimeError(s % (token,))
        if num > self.count:
            s = "Syntax error: Keeping more dice than you are rolling in %s"
            raise RuntimeError(s % (token,))
        if key in 'lL':
            self.filter = lambda l: least(l, num)
        elif key in 'hH':
            self.filter = lambda l: most(l, num)
    def got_modifier(self, scanner, token):
        self.modifier = int(token)
    def got_repeat(self, scanner, token):
        self.repeat = int(token[1:])
    def roll(self, st):
        self.last = st
        self.scanner.scan(st)
        return list(self.finish())
    def reset(self):
        self.count = self.repeat = self.dice = self.modifier = 0
        self.last = ''
        self.filter = None

    def finish(self):
        # set these to defaults in the finish step, not in the init, 
        # so the parser instance can be reused
        if self.count == 0:
            self.count = 1
        if self.repeat == 0:
            self.repeat = 1
        if self.filter == None:
            self.filter = lambda l: l
        if self.dice == 0:
            raise RuntimeError("No die size was given")
        for n in xrange(self.repeat):
            tot = sum(self.filter(
                            [roll(self.dice, 0) for n in xrange(self.count)]
                                  ))
            tot = tot + self.modifier
            yield tot
        self.reset()


def test():
    r = Roller()
    for dice in ['d6xz',  # repeat not a number
                 '1d', '1+2', # left out die size 
                 '1d6l3l3', '1d6h3l3',  # can't specify more than one filter
                 '1d6h+1', # can't leave the die count out of the filter
                 '1d6h2+1', # can't keep more dice than you started with
                 #'1d6+5 1d1' # FIXME, last one doesn't fail correctly
                 ]:
        try:
            r.roll(dice)
        except RuntimeError, e:
            print e
        else:
            assert 0, "%s did not cause an error, and should've" % (dice,)
    print r.roll('d6x3')
    print r.roll('9d6l3-10x2')
    print r.roll('9d6h3+10x2')
    print r.roll('1d  6 x3')
    print r.roll('d 6 -2 x 3')
    print r.roll('2d6-2x1')
    for n in xrange(1000):
        assert 1 <= r.roll('d6')[0] <= 6
        assert 3 <= r.roll('3d6')[0] <= 18
        assert 2 <= r.roll('9d6l3-1x2')[0] <= 17
        assert 4 <= r.roll('9d6h3+1x2')[0] <= 19
        assert 1 <= r.roll('1d  6')[0] <= 6
        assert 3 <= r.roll('d6+2')[0] <= 8
        assert -1 <= r.roll('d 6 -2')[0] <= 4
        assert 4 <= r.roll('2d6+ 2')[0] <= 14
        assert 0 <= r.roll('2d6-2')[0] <= 10
    print 'passed all tests'

def run(argv=None):
    if argv is None:
        argv = sys.argv
    r = Roller()
    while 1:
        try:
            rolled = r.roll(raw_input("Roll: "))
            if len(rolled) > 1:
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
