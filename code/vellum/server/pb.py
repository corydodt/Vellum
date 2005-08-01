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


class MapListener(pb.Referenceable):
    """Make calls on this remote object to push updates across the wire"""
    def __init__(self, map, ):
        self.map = map

    def remote_mapicon_added_event(self, oid, new):
        i = self.map.iconFromId(oid)
        i.__dict__.update(new)
        self.map.icon_added = i
        log.msg("icon added")
    def remote_mapicon_removed_event(self, oid, new):
        i = self.map.iconFromId(oid)
        assert i is not None, 'No icon with id %s found' % (oid,)
        self.map.removeIcon(i)
        self.map.icon_removed = i
        log.msg("icon removed")
    def remote_iconname_event(self, oid, new):
        i = self.map.iconFromId(oid)
        i.iconname = new
        log.msg("iconname changed")
    def remote_iconuri_event(self, oid, new):
        assert None, 'not implemented'
        log.msg("iconimage changed")
    def remote_iconsize_event(self, oid, new):
        i = self.map.iconFromId(oid)
        i.iconsize = new
        log.msg("iconsize changed")
    def remote_iconcorner_event(self, oid, new):
        i = self.map.iconFromId(oid)
        i.iconcorner = new
        log.msg("iconcorner changed")
    def remote_lastwindow_event(self, oid, new):
        self.map.lastwindow = new
        log.msg("lastwindow changed")
    def remote_attention_event(self, oid, new):
        self.map.attention = new
        log.msg("attention changed")
    def remote_scale100px_event(self, oid, new):
        self.map.scale100px = new
        log.msg("scale100px changed")
    def remote_mapname_event(self, oid, new):
        self.map.mapname = new
        log.msg("mapname changed")
    def remote_mapuri_event(self, oid, new):
        assert None, 'not implemented'
        log.msg("image changed")
    def remote_laser_event(self, oid, new):
        self.map.laser = new
        log.msg("laser changed")
    def remote_obscurement_event(self, oid, new):
        assert None, 'not implemented'
        log.msg("obscurement changed")

class Gameboy(pb.Avatar):
    def __init__(self, name):
        cp = ConfigParser.ConfigParser()
        cp.read(fs.ini)

        self.notifiables = []     # MapListener refs from clients

        lastmap = cp.get('vellumpb', 'lastmap', None)
        self.map = Map.loadFromYaml(file(lastmap, 'rb').read())
        self.observable = MapListener(self.map, )

    def perspective_getInitialMap(self):
        return self.map.describeToYaml()

    def perspective_iWantUpdates(self, listener):
        """Here's an object you can use to tell me about map updates"""
        self.notifiables.append(listener)
        return self.observable

    # def dispatchUpdates(self, id, name, new):
    #    for ref in self.notifiables:
    #        ref.callRemote('%s_event' % (name,), id, new)


class GameRealm:
    interface.implements(portal.IRealm)
    def requestAvatar(self, avatarId, mind, *interfaces):
        if pb.IPerspective not in interfaces:
            raise NotImplementedError
        return pb.IPerspective, Gameboy(avatarId), lambda:None

c = checkers.InMemoryUsernamePasswordDatabaseDontUse(jezebel='X',
                                              gm='X',
                                              )
gameportal = portal.Portal(GameRealm())
gameportal.registerChecker(c)

