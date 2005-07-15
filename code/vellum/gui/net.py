"""HTTP and PB client."""

import md5

from twisted.internet import reactor, defer
from twisted.spread import pb
from twisted.python import log
from twisted.web.client import downloadPage

from vellum.gui.fs import fs
from vellum.server import HTTPPORT, PBPORT

def _cb_connected(pbobject):
    log.msg('connected %s' % (repr(pbobject,)))
    return pbobject


from gtkmvc import model
from vellum.gui.ctlutil import SilentController


class NetModel(model.Model):
    __properties__ = {'server': None
                      }



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
            if info['type'] == 'map':
                self.map.mapname = info['name']
                self.map.lastwindow = info['view']
            elif info['type'] == 'character':
                icon = self.map.addIcon(info['name'], info['size'])
                if info['corner'] is not None:
                    self.map.moveIcon(icon, *info['corner'])
            elif info['type'] == 'mask/obscurement':
                self.map.obscurement = None # TODO

    def pb_gotMapInfo(self, map):
        fileiter = iter(map['files'])
        d = defer.maybeDeferred(self._getNextFile, fileiter)
        d.addCallback(lambda _: map['files'])
        return d

    def _getNextFile(self, fileinfos):
        try:
            fi = fileinfos.next()
            try:
                # do we already have the file? let's find out.
                self.checkFile(fi)
                return defer.maybeDeferred(self._getNextFile, fileinfos)
            except ValueError:
                log.msg('Getting file at %s' % (fi['uri'],))
                uri = 'http://%s:%s/%s' % (self.netmodel.server,
                                           HTTPPORT,
                                           fi['uri'],
                                           )
                return downloadPage(uri, fs.downloads(fi['name'])
                        ).addErrback(log.err
                        ).addCallback(lambda _: self.checkFile(fi)
                        ).addCallback(lambda _: self._getNextFile(fileinfos)
                        )
        except StopIteration:
            return

    def checkFile(self, fileinfo):
        try:
            f = file(fs.downloads(fileinfo['name']), 'rb')
            digest = md5.md5(f.read()).hexdigest()
            print 'Got file; checksum:', digest
            if digest == fileinfo['md5']:
                print 'md5 ok for %s' % (fileinfo['name'],)
                return
        except EnvironmentError:
            # Missing/unreadable files will fall through to 
            # raise ValueError (otherwise caller has to check for both kinds
            # of exception, which is pointless)
            pass
        raise ValueError("File was not received correctly: %s" % (
            str(fileinfo),))
        
