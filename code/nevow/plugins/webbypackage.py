from twisted.python import util
from nevow import athena
import webby

def _f(*sib):
    return util.sibpath(webby.__file__, '/'.join(sib))

webbyPkg = athena.JSPackage({
    'WebbyVellum': _f('webby.js'),
    ## 'WebbyVellum.Tests': _f('webby', 'livetest_webby.js'),
    'Tabby': _f('tab.js'),
    'Tabby.Tests': _f('livetest_tab.js')
    })

