"""HTTP and PB client."""

import re

from twisted.internet import reactor, defer
from twisted.spread import pb
from twisted.python import log
from twisted.web.client import downloadPage

from gtkmvc import model

from vellum.gui.fs import fs, cache
from vellum.server import HTTPPORT, PBPORT
from vellum.server.map import Map
from vellum.server.pb import MapListener
from vellum.util.ctlutil import SilentController


class NetModel(model.Model):
    __properties__ = {'server': None,
                      'map': None,
                      }

class NetClient(SilentController):
    _prop_pattern = re.compile(r'property_(?P<prop>.*)_change_notification', )

    def __getattr__(self, name):
        """Route changes to the map through my MapListener"""
        m = self._prop_pattern.match(name)
        if m is not None:
            prop = m.group('prop')
            return lambda m,o,n: self.updateListener(prop, m, n)
        raise AttributeError(name)

    def updateListener(self, propname, model, value):
        if self.remote_listener is not None:
            d = self.remote_listener.callRemote("%s_event" % (propname,), 
                                                model.id, value)
            # TODO - wait for d?

    def __init__(self, netmodel):
        self.pbfactory = pb.PBClientFactory()
        self.remote_listener = None
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
        d.   addCallback(lambda listener: 
                self.remote.callRemote('iWantUpdates', listener))
        d.    addCallback(self.receivedListener)
        d.     addCallback(lambda _: self.collectFiles())
        d.addErrback(lambda reason: log.err(reason))
        return d

    def gotMapData(self, data):
        map = Map.loadFromYaml(data)
        self.netmodel.map = map

        log.msg("Received map, bringing view up to date!!")
        # force updates to the model to take effect immediately
        map.mapname = map.mapname
        map.mapuri = map.mapuri
        map.lastwindow = map.lastwindow
        map.scale100px = map.scale100px
        map.registerObserver(self)
        for icon in map.icons:
            icon.iconuri = icon.iconuri
            icon.iconname = icon.iconname
            icon.iconsize = icon.iconsize
            if icon.iconcorner is not None:
                icon.iconcorner = icon.iconcorner
            icon.registerObserver(self)
        # TODO: drawings, notes, sounds
        return MapListener(map)


    def receivedListener(self, remote_listener):
        self.remote_listener = remote_listener

    def collectFiles(self):
        return defer.maybeDeferred(self._getNextFile, 
                                   self.netmodel.map.iterUris())

    def _getNextFile(self, fileinfos):
        try:
            uri = fileinfos.next()
            # do we already have the file? let's find out.
            if uri in cache:
                # yep, we do. next!
                log.msg('Found %s cached' % (uri,))
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
