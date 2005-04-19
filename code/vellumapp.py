#!python
import sys, os
# this must happen first because reactors are magikal
from twisted.internet import gtk2reactor
gtk2reactor.install()
from twisted.internet import reactor, defer
from twisted.python import log, usage

from vellum.gui.frontend import FrontEnd
from vellum.gui.net import NetClient

import gtk

class Options(usage.Options):
    synopsis = 'Usage: vellumapp.py [options]'
    optParameters = [['fps', None, 15, 'Frames per second'],
                     ['logfile', 'l', None, 'File to use for logging'],
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
    netclient = NetClient()
    gui = FrontEnd(d, netclient, o['fps'])
    d.addCallback(finish).addErrback(finish)

    reactor.run()
    # #@!@# -- without the following, we can't quit the app after an error.
    reactor.suggestThreadPoolSize(0)


if __name__ == '__main__':
    run()
