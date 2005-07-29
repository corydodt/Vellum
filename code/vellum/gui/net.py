"""HTTP and PB client."""

from twisted.internet import reactor, defer
from twisted.spread import pb
from twisted.python import log
from twisted.web.client import downloadPage

from gtkmvc import model

from vellum.gui.fs import fs, cache
from vellum.server import HTTPPORT, PBPORT
from vellum.server.map import Map
from vellum.server.pb import MapListener
from vellum.gui.ctlutil import SilentController


class NetModel(model.Model):
    __properties__ = {'server': None
                      }

class NetClient(SilentController):
    def __init__(self, netmodel):
        self.pbfactory = pb.PBClientFactory()
        self.listener = None
        self.map = None

        netmodel.registerObserver(self)
        self.netmodel = netmodel

    def property_server_change_notification(self, model, old, new):
        self.connectPB(new, PBPORT)

    def _cb_connected(self, ref):
        assert hasattr(ref, 'callRemote'), 'Not connected: %s' % (ref,)
        log.msg('connected %s' % (repr(ref,)))
        self.remote = ref
        return ref


    def connectPB(self, server, port):
        reactor.connectTCP(server, port, self.pbfactory)
        d = self.pbfactory.getRootObject()
        d.addCallback(self._cb_connected)
        d. addCallback(lambda _: self.remote.callRemote('getInitialMap'))
        d.  addCallback(self.gotMapData)
        d.   addCallback(lambda _: self.remote.callRemote('iWantUpdates', 
                                                          self.listener))
        d.    addCallback(self.receivedListener)
        d.     addCallback(lambda _: self.collectFiles())
        d.addErrback(lambda reason: log.err(reason))
        return d

    def gotMapData(self, data):
        self.map = Map.loadFromYaml(data)
        self.map.registerObserver(self)
        self.listener = MapListener(self.map)

    def receivedListener(self, listener):
        self.listener = listener

    def collectFiles(self):
        return defer.maybeDeferred(self._getNextFile, self.map.iterUris())

    def _getNextFile(self, fileinfos):
        try:
            uri = fileinfos.next()
            # do we already have the file? let's find out.
            if uri in cache:
                # yep, we do. next!
                return defer.maybeDeferred(self._getNextFile, fileinfos)
            else:
                # no, don't have the file.
                server_st = 'http://%s:%s' % (self.netmodel.server, HTTPPORT)
                auri = uri.replace('$SERVER', server_st)
                log.msg('Getting file at %s' % (auri,))
                cache_name = cache.reserve(uri)
                return downloadPage(auri, cache_name
                        ).addErrback(log.err
                        ).addCallback(
                                lambda _: self._getNextFile(fileinfos)
                        )
        except StopIteration:
            return
