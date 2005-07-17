"""Convert real world distances into normal units.
Uses metric units, with conversions.
"""
from __future__ import division

import pyparsing as P

CL = P.CaselessLiteral
Sup = P.Suppress

# optional unit endings in lieu of real stemming ;-)
OPS = P.Optional(CL('s'))
OPES = P.Optional(CL('es'))
OPD = P.Optional('.')

def getUnitConversion(name):
    return lambda s,p,t: name

# setParseAction should convert the unit name into something which is 
# a key of factors (below)
meter = CL('meter') + OPS | CL('metre') + OPS | CL('m') + OPD
meter.setParseAction(getUnitConversion('meter'))
cm = CL('centimeter') + OPS | CL('centimetre') + OPS | CL('cm') + OPD
cm.setParseAction(getUnitConversion('cm'))
mm = CL('millimeter') + OPS | CL('millimetre') + OPS | CL('mm') + OPD
mm.setParseAction(getUnitConversion('mm'))
km = CL('kilometer') + OPS | CL('kilometre') + OPS | CL('km') + OPD
km.setParseAction(getUnitConversion('km'))
yard = CL('yard') + OPS | CL('yd') + OPD | CL('y') + OPD
yard.setParseAction(getUnitConversion('yard'))
inch = CL('inch') + OPES | CL('in') + OPD | CL('"')
inch.setParseAction(getUnitConversion('inch'))
mile = CL('mile') + OPS | CL('mi') + OPD
mile.setParseAction(getUnitConversion('mile'))
foot = CL('foot') | CL('feet') | CL('ft') + OPD | CL("'")
foot.setParseAction(getUnitConversion('foot'))

# add other units as needed?
unit = (meter ^ cm ^ mm ^ km ^ mile ^ yard ^ inch ^ foot).setResultsName('unit')

number = P.Word(P.nums + '.').setResultsName('number')
number.setParseAction(lambda s,p,t: map(float, t))

distance = number + unit + P.StringEnd()

# common conversion factors
factors = dict(meter = 1.000,
               km = 1000.000,
               mm = 0.001,
               cm = 0.010,

               foot = 0.3048,
               mile = 1609.344,
               yard = 0.9144,
               inch = 0.0254,
               )

def normalize(dist):
    """Convert the unit string into a floating point in meters"""
    res = distance.parseString(dist)
    return convert(res.number, res.unit[0], 'meter')

def convert(amt, unitfrom, unitto):
    """Convert amt from one unit to another"""
    return amt * factors[unitfrom] / factors[unitto]

def test():
    cnv = lambda amt, uf, ut: round(convert(amt, uf, ut), 3)
    assert cnv(15, 'meter', 'km') == 0.015
    assert cnv(15, 'meter', 'inch') == 590.551
    assert cnv(15, 'yard', 'inch') == 540.000
    assert cnv(15, 'yard', 'cm') == 1371.6
    assert cnv(15, 'mm', 'yard') == 0.016
    assert cnv(15, 'foot', 'cm') == 457.2
    assert cnv(15, 'mile', 'km') == 24.140

    norm = lambda s: round(normalize(s), 3)
    assert norm("15'") == 4.572
    assert norm("15 '") == 4.572
    assert norm('12 "') == 0.305
    assert norm('7 ft') == 2.134
    assert norm('7 ft .') == 2.134
    assert norm('2.1 yd.') == 1.920
    assert norm('18mi.') == 28968.192
    assert norm("2.5'") == 0.762
    assert norm("2.5ft") == 0.762
    assert norm("2.5centimetres") == 0.025
    assert norm("2.5mm") == 0.003

    print 'passed'

if __name__ == '__main__':
    test()
