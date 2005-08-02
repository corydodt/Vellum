"""HTTP and PB client."""

import re
import ConfigParser

from twisted.internet import reactor, defer
from twisted.spread import pb
from twisted.python import log
from twisted.web.client import downloadPage
from twisted.cred import credentials

from gtkmvc import model

from vellum.gui.fs import fs, cache
from vellum.server import HTTPPORT, PBPORT
from vellum.server.map import Map
from vellum.server.pb import MapView
from vellum.util.ctlutil import SilentController


class NetModel(model.Model):
    __properties__ = {'server': None,
                      'recent_servers': [],
                      'map': None,
                      'username': None,
                      }
    def saveIni(self):
        options = {'username': self.username, 
                   'recent_servers': ' '.join(self.recent_servers),
                   }
        cp = ConfigParser.ConfigParser()
        cp.add_section('vellum')
        for k,v in options.items():
            cp.set('vellum', k, v)
        cp.write(file(fs.ini, 'w'))



class NetClient(SilentController):
    _prop_pattern = re.compile(r'property_(?P<prop>.*)_change_notification', )

    def __init__(self, netmodel):
        self.pbfactory = pb.PBClientFactory()
        self.remote_control = None
        self.map = None

        netmodel.registerObserver(self)
        self.netmodel = netmodel

    def __getattr__(self, name):
        """Route changes to the map through my MapView"""
        m = self._prop_pattern.match(name)
        if m is not None:
            prop = m.group('prop')
            return lambda m,o,n: self.updateListener(prop, m, n)
        raise AttributeError(name)

    def updateListener(self, propname, model, value):
        if self.remote_control is not None:
            d = self.remote_control.callRemote("%s_event" % (propname,), 
                                               model.id, value)
            # TODO - wait for d?

    def property_server_change_notification(self, model, old, new):
        self.connectPB(new, PBPORT)

    def property_map_change_notification(self, model, old, new):
        pass

    def _cb_connected(self, avatar):
        assert hasattr(avatar, 'callRemote'), 'Not connected: %s' % (avatar,)
        log.msg('connected %s' % (repr(avatar,)))
        self.avatar = avatar
        return avatar


    def connectPB(self, server, port):
        reactor.connectTCP(server, port, self.pbfactory)

        self.map_view = MapView()
        creds = credentials.UsernamePassword(self.netmodel.username, 'X')
        d = self.pbfactory.login(creds, self.map_view)

        d.addCallback(self._cb_connected)
        d. addCallback(lambda _: self.avatar.callRemote('getInitialMap'))
        d.  addCallback(self.gotMap)
        d.   addCallback(lambda _: self.collectFiles())
        d.addErrback(lambda reason: log.err(reason))
        return d

    def gotMap(self, (data, remote_control)):
        self.remote_control = remote_control

        map = Map.loadFromYaml(data)
        self.netmodel.map = map
        self.map_view.map = map

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
