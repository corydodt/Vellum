from twisted.python import util
from nevow import athena
import webby

def _f(*sib):
    return util.sibpath(webby.__file__, '/'.join(sib))

webbyPkg = athena.JSPackage({
    'WebbyVellum': _f('ircweb.js'),
    'WebbyVellum.Tests': _f('test', 'livetest_ircweb.js'),

    'Tabby': _f('tabs.js'),
    'Tabby.Tests': _f('test', 'livetest_tabs.js'),

    'Windowing': _f('windowing.js'),
    'Windowing.Tests': _f('test', 'livetest_windowing.js'),

    'DeanEdwards': _f('events.js'),
    })

