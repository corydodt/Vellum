#!python
import warnings
warnings.filterwarnings('ignore')


import sys

import ConfigParser

# install must happen first because reactors are magikal
from twisted.internet import gtk2reactor
gtk2reactor.install()
from twisted.internet import reactor, defer
from twisted.python import log, usage

from vellum.gui.net import NetClient, NetModel
from vellum.gui.view import BigController, BigView
from vellum.gui.fs import fs

class Options(usage.Options):
    synopsis = 'Usage: Vellum.py [options]'
    optParameters = [['logfile', 'l', None, 'File to use for logging'],
                     ]

def finish(fail, model):
    """This doubles as callback and errback"""
    try:
        if fail is not None:
            log.err(fail)
    finally:
        try:
            model.saveIni()
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

    cp = ConfigParser.ConfigParser()
    cp.read(fs.ini)
    options = dict(cp.items('vellum'))

    
    netmodel = NetModel()
    netclient = NetClient(netmodel, )

    bigctl = BigController(netmodel, d)
    bigview = BigView(bigctl)

    netmodel.username = options['username']
    netmodel.recent_servers = options['recent_servers'].split()


    d.addCallback(finish, netmodel).addErrback(finish, netmodel)

    reactor.run()

if __name__ == '__main__':
    run()
