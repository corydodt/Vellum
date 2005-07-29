#!python
import warnings
warnings.filterwarnings('ignore')


import sys
# install must happen first because reactors are magikal
from twisted.internet import gtk2reactor
gtk2reactor.install()
from twisted.internet import reactor, defer
from twisted.python import log, usage

from vellum.server.map import Map
from vellum.gui.net import NetClient, NetModel
from vellum.gui.view import BigController, BigView

class Options(usage.Options):
    synopsis = 'Usage: vellumapp.py [options]'
    optParameters = [['logfile', 'l', None, 'File to use for logging'],
                     ]

def finish(fail=None):
    try:
        if fail is not None:
            log.err(fail)
    finally:
        reactor.stop()

def run(argv = None):
    if argv is None:
        argv = sys.argv
    o = Options()
    o.parseOptions(argv[1:])
    try:
        logfile = file(o['logfile'], 'w+')
        log.startLogging(logfile)
    except (TypeError, EnvironmentError):
        log.startLogging(sys.stderr)

    d = defer.Deferred()

    
    netmodel = NetModel()
    netclient = NetClient(netmodel)

    bigctl = BigController(netmodel, d)
    bigview = BigView(bigctl)


    d.addCallback(finish).addErrback(finish)

    # FIXME reactor.callLater(1, _setServer, netmodel)

    reactor.run()

def _setServer(netmodel):
    """FIXME - set a server so we can test things out"""
    netmodel.server = '127.0.0.1'

if __name__ == '__main__':
    run()
