from twisted.python import util
from nevow import athena
import webby

def _f(*sib):
    return util.sibpath(webby.__file__, '/'.join(sib))

webbyPkg = athena.JSPackage({
    'WebbyVellum': _f('webby.js'),
    ## 'WebbyVellum.Tests': _f('livetest_webby.js'),
    'Tabby': _f('tabs.js'),
    'Tabby.Tests': _f('livetest_tabs.js'),
    'DeanEdwards': _f('events.js')
    })

