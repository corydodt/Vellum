"""HTTP and PB client."""

import md5

from twisted.internet import reactor, defer
from twisted.spread import pb
from twisted.python import log
from twisted.web.client import downloadPage

from vellum.gui.fs import fs
from vellum.server import HTTPPORT, PBPORT
from vellum.util import distance

def _cb_connected(pbobject):
    log.msg('connected %s' % (repr(pbobject,)))
    return pbobject


from gtkmvc import model
from vellum.gui.ctlutil import SilentController


class NetModel(model.Model):
    __properties__ = {'server': None
                      }


class FileInfo:
    """An intermediate storage for data and operations read from map files"""
    def __init__(self, info):
        self.info = info
        if info['type'].startswith('mask/'):
            _type = info['type'][5:]
            self.cache_name = '%s (%s)' % (info['name'], _type)
        else:
            self.cache_name = info['name']
        self.md5 = info['md5']
        self.uri = info['uri']

    def unpack(self, map):
        """Set values in map based on my data"""
        _type = self.info['type'].replace('/', '_')
        unpacker = getattr(self, 'unpack_%s' % (_type,))
        unpacker(map)

    def unpack_map(self, map):
        map.mapname = self.info['name']
        map.lastwindow = self.info['view']
        map.scale = distance.normalize(self.info['scale100px'])

    def unpack_character(self, map):
        icon = map.addIcon(self.info['name'], self.info['size'])
        if self.info['corner'] is not None:
            map.moveIcon(icon, *self.info['corner'])
        icon.size = distance.normalize(self.info['size'])

    def unpack_mask_obscurement(self, map):
        pass



class NetClient(SilentController):
    def __init__(self, map, netmodel):
        self.pbfactory = pb.PBClientFactory()
        map.registerObserver(self)
        self.map = map

        netmodel.registerObserver(self)
        self.netmodel = netmodel

    def property_server_change_notification(self, model, old, new):
        self.connectPB(new, PBPORT)

    def connectPB(self, server, port):
        reactor.connectTCP(server, port, self.pbfactory)
        d = self.pbfactory.getRootObject()
        d.addErrback(lambda reason: 'error: '+str(reason.value))
        d.addCallback(_cb_connected)
        d.addCallback(lambda pbobject: 
                        pbobject.callRemote('listAvailableFiles')
                      )
        d.addCallback(self.pb_gotMapInfo)
        d.addCallback(self.pb_gotAllFiles)
        return d

    def pb_gotAllFiles(self, files):
        for info in files:
            info.unpack(self.map)

    def pb_gotMapInfo(self, mapdata):
        infos = map(FileInfo, mapdata['files'])
        d = defer.maybeDeferred(self._getNextFile, iter(infos))
        d.addCallback(lambda _: infos)
        return d

    def _getNextFile(self, fileinfos):
        try:
            fi = fileinfos.next()
            try:
                # do we already have the file? let's find out.
                self.checkFile(fi)
                return defer.maybeDeferred(self._getNextFile, fileinfos)
            except ValueError:
                log.msg('Getting file at %s' % (fi.uri,))
                uri = 'http://%s:%s/%s' % (self.netmodel.server,
                                           HTTPPORT,
                                           fi.uri,
                                           )
                return downloadPage(uri, fs.downloads(fi.cache_name)
                        ).addErrback(log.err
                        ).addCallback(lambda _: self.checkFile(fi)
                        ).addCallback(lambda _: self._getNextFile(fileinfos)
                        )
        except StopIteration:
            return

    def checkFile(self, fileinfo):
        try:
            f = file(fs.downloads(fileinfo.cache_name), 'rb')
            digest = md5.md5(f.read()).hexdigest()
            print 'Got file; checksum:', digest
            if digest == fileinfo.md5:
                print 'md5 ok for %s' % (fileinfo.cache_name,)
                return
        except EnvironmentError:
            # Missing/unreadable files will fall through to 
            # raise ValueError (otherwise caller has to check for both kinds
            # of exception, which is pointless)
            pass
        raise ValueError("File was not received correctly: %s" % (
            str(fileinfo),))
        
