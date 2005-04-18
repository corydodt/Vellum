import sys, os
# this must happen first because reactors are magikal
from twisted.internet import gtk2reactor
gtk2reactor.install()
from twisted.internet import reactor, defer
from twisted.python import log, usage, failure

from frontend import FrontEnd
from net import NetClient

class Options(usage.Options):
    synopsis = 'Usage: vellumapp.py [options]'
    optParameters = [['fps', None, 15, 'Frames per second'],
                     ['logfile', 'l', None, 'File to use for logging'],
                     ]

def quitWithMessage(fail=failure.Failure()):
    log.err(fail)
    gtk.main_quit()



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
    d.addCallback(lambda _: gui.quit()).addErrback(quitWithMessage)

    reactor.run()

if __name__ == '__main__':
    run()
