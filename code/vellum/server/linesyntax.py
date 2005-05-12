r"""Define the syntax for parsing statements on IRC.
Lines beginning with . are commands, unless the next significant character is
a dot as well.
Lines that are not commands may contain the following syntax:
    - A single word beginning with a letter and prefixed by a * anywhere in
      the line is the name of an NPC or a PC.
    - An expression inside brackets [] or braces {} is a verb.
    - A verb starts with zero or more verbnames, and ends with a dice
      expression.
    - A dice expression obeys the following regex (verbose, whitespace ignored):
\[0-9\]* (d\s*[0-9]+)? ((\+|\-)\s*[0-9]+)? ([lLhH]\s*[0-9]+)? ([Xx]\s*[0-9]+)?
count    size          modifier            filter             repeat
      So all of the following are valid dice expressions:
        5    5x3    5+1x3    d6    3d6     9d6l3-1x2    d6+2
    - 
"""


<Shara> I [attack 1d6+1] vs grimlock1
<DM> *grimlock1 [attack 1d2+10]s vs shara
<Rade> I [cast] a [fireball] vs grimlock1, grimlock2
