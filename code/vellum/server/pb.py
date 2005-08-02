"""The PB service of the vellum server.
PLEASE BE CAREFUL.
Removing any of the remote_ methods here, or changing any of their return
values, will result in incompatible network changes.  Be aware of that and
try to minimize incompatible network changes.

At some point in the future, there will be a policy about what changes are
allowed in what versions.
"""
import ConfigParser

from twisted.spread import pb
from twisted.cred import checkers, portal
from twisted.python import log

from zope import interface

from vellum.server.map import Map, Icon
from vellum.server.fs import fs

class MapView(pb.Viewable):
    """Make calls on this remote object to push updates across the wire"""
    def __getattr__(self, name):
        if name.startswith('view_') and name.endswith('_event'):
            if getattr(self, 'map', None) is None:
                raise RuntimeError("%r: map is not set" % (self,))
            return getattr(self, name[5:])
        raise AttributeError(name)
    def mapicon_added_event(self, perspective, oid, new):
        i = self.map.iconFromId(oid)
        i.__dict__.update(new)
        self.map.icon_added = i
        log.msg("icon added")
    def mapicon_removed_event(self, perspective, oid, new):
        i = self.map.iconFromId(oid)
        assert i is not None, 'No icon with id %s found' % (oid,)
        self.map.removeIcon(i)
        self.map.icon_removed = i
        log.msg("icon removed")
    def iconname_event(self, perspective, oid, new):
        i = self.map.iconFromId(oid)
        i.iconname = new
        log.msg("iconname changed")
    def iconuri_event(self, perspective, oid, new):
        assert None, 'not implemented'
        log.msg("iconimage changed")
    def iconsize_event(self, perspective, oid, new):
        i = self.map.iconFromId(oid)
        i.iconsize = new
        log.msg("iconsize changed")
    def iconcorner_event(self, perspective, oid, new):
        i = self.map.iconFromId(oid)
        i.iconcorner = new
        log.msg("iconcorner changed")
    def lastwindow_event(self, perspective, oid, new):
        self.map.lastwindow = new
        log.msg("lastwindow changed")
    def attention_event(self, perspective, oid, new):
        self.map.attention = new
        log.msg("attention changed")
    def scale100px_event(self, perspective, oid, new):
        self.map.scale100px = new
        log.msg("scale100px changed")
    def mapname_event(self, perspective, oid, new):
        self.map.mapname = new
        log.msg("mapname changed")
    def mapuri_event(self, perspective, oid, new):
        assert None, 'not implemented'
        log.msg("image changed")
    def laser_event(self, perspective, oid, new):
        self.map.laser = new
        log.msg("laser changed")
    def obscurement_event(self, perspective, oid, new):
        assert None, 'not implemented'
        log.msg("obscurement changed")

class Gameboy(pb.Avatar):
    def __init__(self, name, peers):
        cp = ConfigParser.ConfigParser()
        cp.read(fs.ini)

        self.peers = peers

        lastmap = cp.get('vellumpb', 'lastmap', None)
        self.map = Map.loadFromYaml(file(lastmap, 'rb').read())
        self.observable = MapView()
        self.observable.map = self.map

    def perspective_getInitialMap(self):
        return self.map.describeToYaml(), self.observable


class GameRealm:
    interface.implements(portal.IRealm)
    def __init__(self):
        self.clients = []

    def requestAvatar(self, avatarId, mind, *interfaces):
        if pb.IPerspective not in interfaces:
            raise NotImplementedError
        avatar = Gameboy(avatarId, self.clients)
        self.clients.append(mind)
        return pb.IPerspective, avatar, lambda:self.clients.remove(mind)

c = checkers.InMemoryUsernamePasswordDatabaseDontUse(jezebel='X',
                                                     gm='X',
                                                     )
gameportal = portal.Portal(GameRealm())
gameportal.registerChecker(c)

