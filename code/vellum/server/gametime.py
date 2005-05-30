"""Classes for customizing and advancing time

Default clock used is earth-like: 365 days in a year, 24 hours in a day,
time divided unto the seconds, single 28 day lunar cycle, weeks and months
named as in English.  This is deceptive though, as the default clock will
*not* give the correct dates or days of the week for any given offset.  This
is because leap days are not supported.
"""

# time format parsing
import pyparsing as P
Sup = P.Suppress

identifier = P.Word(P.alphas+"_", P.alphanums+"_"
                    ).setResultsName('identifier')
format_name = (Sup(P.Literal('$')) + identifier)

class Clock:
    """The gametime clock for a session."""
    def __init__(self):
        self.time = 0
        self.formatters = {}
        self.syncs = {}

    def set(self, units):
        self.time = units

    def __add__(self, other):
        clock = Clock()
        clock.set(self.time + other)
        return clock
    def __sub__(self, other):
        clock = Clock()
        clock.set(self.time - other)
        return clock


    def __iadd__(self, other):
        self.time = self.time + other
        return self
    def __isub__(self, other):
        self.time = self.time - other
        return self

    def __div__(self, other):
        return self.time / other.length
    __truediv__ = __div__ 

    def __mod__(self, other):
        if hasattr(other, 'periodStart'):
            start = other.periodStart(self.time)
            return self.time%other.length - start
        else:
            return self.time % other.length

    def resolveTimeString(self, s, loc, toks):
        unit = toks[0]
        # if unit is a cycle, sync is the offset gets added to the cycle
        # to make it synchronize with time 0
        sync = self + self.syncs.get(unit, 0)
        return '%s' % (self.formatters[unit](sync),)

    def format(self, formatstring):
        """Pass strings as $year or $weekday."""
        # make a copy of the global parser so i can specify parseActions
        # locally
        format = format_name.copy()
        format.setParseAction(self.resolveTimeString)

        print format.transformString(formatstring)


    def synchronize(self, formatname, offset):
        """Begin cycle at offset units from 0.  This is useful in case
        January 1 is a Wednesday, for example. You would do:
        >>> clock.synchronize(week, day*3)
        """
        self.syncs[formatname] = offset


    def setFormatter(self, name, function):
        """Add a named formatter to the clock.  
        "function" is a callable taking one argument.  It will be passed
        an instance of the clock object and should return a string.
        """
        self.formatters[name] = function



class Unit:
    """A unit of time."""
    def __init__(self, name, length):
        self.name = name
        self.length = length

    def __mul__(self, other):
        offset = getattr(other, 'length', other)
        return self.length * offset

    def __add__(self, other):
        return self.length + other

    def __rdiv__(self, other):
        return other / self.length



class Cycle(Unit):
    """A sequence of time units of varying durations, with names"""
    def __init__(self, name, subname, durations, names):
        self.name = name
        self.subname = subname
        self.periods = zip(durations, names)
        self.length = sum(durations)

    def iteratePeriods(self, function, offset):
        """call function with the start of the period and name of the period
        given by the offset"""
        offset = offset % self.length
        now = 0
        for duration, name in self.periods:
            if now + duration > offset:
                return function(now, name)
            now = now + duration

    def periodStart(self, offset):
        """Return the offset for the start of the period in which offset
        falls."""
        return self.iteratePeriods((lambda start, name: start), offset)

    def describe(self, offset):
        """Give the name of the cycle phase which is given by offset"""
        return self.iteratePeriods((lambda start, name: name), offset)





second = Unit("second", 1)
round = Unit("round", second * 6)
minute = Unit("minute", second*60)
hour = Unit("hour", minute*60)
day = Unit("day", hour*24)
daylight = Cycle("periods of day", "daylight", 
                 [hour*3,       hour*3,    hour*6,    hour*1, hour*4,
                  hour*2,    hour*5],
                 ["late at night", "predawn", "in the morning", "around noon", 
                  "in the afternoon", "in the evening", "at night"])
week = Cycle("week", "weekday", 
             [day*1]*7, 
             ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday",
              "Friday", "Saturday"])
months = Cycle("months", "month", 
               [day*31, day*28, day*31, day*30, day*31, day*30, day*31, day*31, 
                day*30, day*31, day*30, day*31],
               ["January", "February", "March", "April", "May", "June", "July", 
                "August", "September", "October", "November", "December"])
lunarcycle = Cycle("lunar period", "phase", 
                   [day*1, day*6, day*1, day*6, day*1, day*6, day*1, day*6],
                   ["new", "waxing crescent", "first quarter", "waxing gibbous",
                    "full", "waning gibbous", "last quarter", "waning cresent"
                    ])
year = Unit("year", day*365)


clock = Clock()
clock.set(year*2005 + day*149 + hour*12)
clock += hour*4
clock = clock - hour*4
clock = clock + hour*5


clock.setFormatter('year', lambda c: c/year)
clock.setFormatter('month', lambda c: months.describe(c.time))
clock.setFormatter('hour', lambda c: c%day/hour)
clock.setFormatter('daylight', lambda c: daylight.describe(c.time))
clock.setFormatter('weekday', lambda c: week.describe(c.time))
clock.synchronize('weekday', day*3)
clock.setFormatter('monthday', lambda c: c%months/day+1)
clock.setFormatter('moon', lambda c: lunarcycle.describe(c.time))

clock.format("Year $year, $month $monthday, Hour $hour, $daylight.  It is $weekday.")
clock += hour*40
clock.format("Year $year, $month $monthday, Hour $hour. The moon tonight is $moon.")
clock += day * 14
clock.format("Year $year, $month $monthday, Hour $hour.  It is $weekday.  The moon tonight is $moon.")
