"""Every IRC client needs some /slash commands."""

import pyparsing as P
L = P.Literal
Sup = P.Suppress

commandWord = P.Word(P.alphanums+'_').setResultsName('commandWord')

commandLeader = L('/')

commandArgs = P.restOfLine.setResultsName('commandArgs')

command = (P.StringStart() + 
           Sup(commandLeader) + 
           commandWord + 
           P.Optional(Sup(P.White()) + commandArgs)
           ).setResultsName('command')

nonCommand = (P.StringStart() + P.restOfLine).setResultsName('nonCommand')

line = (command | nonCommand)

tests = [('hello', 'nonCommand'),
('/me says hi', 'command'),
('/123', 'command'),
('/abc1_ sas', 'command'),
('hi /abc1_ sas', 'nonCommand'),
('/** sup **/', 'nonCommand'),
('/', 'nonCommand'),
('hello /there', 'nonCommand'),
]

def simpleTest():
    for t, expected in tests:
        print t, 
        print '|||', 
        print line.parseString(t).getName() == expected

commandTests = [
('/me says hi', 'me'),
('/123', '123'),
('/abc1_ sas', 'abc1_'),
]

def commandTest():
    for t, expected in commandTests:
        print t,
        print '|||',
        print line.parseString(t).commandWord == expected
        

if __name__ == '__main__':
    simpleTest()
    commandTest()

