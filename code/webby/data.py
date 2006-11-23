import sys, os
from decimal import Decimal

from twisted.application import service
from twisted.python.filepath import FilePath
from twisted.python import log

from axiom import store, substore, item, attributes as A

from zope.interface import Interface, implements

if sys.platform == 'win32':
    appdata = FilePath(os.path.join(os.environ['APPDATA'], 'Vellum'))
else:
    appdata = FilePath(os.path.join(os.environ['HOME'], '.vellum'))

class DataService(item.Item, service.Service, item.InstallableMixin):
    schemaVersion = 1
    smtpFrom = A.text()
    smtpServer = A.text()

    parent = A.inmemory()
    running = A.inmemory()

    def installOn(self, other):
        super(DataService, self).installOn(other)
        other.powerUp(self, service.IService)
        if self.parent is None:
            self.setServiceParent(other)

    def startService(self):
        log.msg("Starting service %r in %s" % (self, appdata,))

        # TODO - substores are going to be kept in zipfiles, which can
        # be opened from anywhere you want and used as substores from
        # the temp directory where they will be unpacked.
        # Until that is implemented, this is hardcoded.
        ## self.substore = store.Store(appdata.child('gnoll.axiom'))

class IArticle(Interface):
    """
    A thing you can put on a map, such as a character or sound effect node
    """

class _ArticleMixin(object):
    implements(IArticle)

    def installOn(self, other):
        other.powerUp(self, IArticle)

class Map(item.Item):
    """
    The Map that a game is played on, with information about its physical
    characteristics.
    """
    schemaVersion = 1
    name = A.text(allowNone=False)
    path = A.path(allowNone=False, relative=True)
    scale100px = A.point4decimal() # Distance in meters of 100 map px @ 100% zoom


class Character(item.Item, _ArticleMixin):
    """A player character or NPC"""
    schemaVersion = 1
    name = A.text(allowNone=False)
    path = A.path(allowNone=False, relative=True)
    top = A.point4decimal()
    left = A.point4decimal()
    scale = A.point4decimal(allowNone=False)

class User(item.Item):
    schemaVersion = 2
    email = A.text("The username used to log in", allowNone=False)
    nick = A.text("The default nick to use in IRC")
    firstname = A.text()
    lastname = A.text()
    password = A.text()
    confirmationKey = A.text()
    unconfirmedPassword = A.text("Password is held here until confirmationKey is validated.")

class FileMeta(item.Item):
    """A file that has been uploaded."""
    schemaVersion = 1
    data = A.reference()
    thumbnail = A.reference()
    filename = A.text()
    mimeType = A.text()
    md5 = A.text()
    user = A.reference()
    width = A.integer()
    height = A.integer()

class FileData(item.Item):
    schemaVersion = 1
    data = A.bytes()

    def __repr__(self):
        return '<FileData @%x>' % (id(self),)
