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
    smtpFrom = A.text(doc="The email address used as From: in emails")
    smtpServer = A.text(doc="The SMTP server used for outgoing email")

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
    email = A.text(doc="The username used to log in", allowNone=False)
    nick = A.text(doc="The default nick to use in IRC")
    firstname = A.text(doc="The first name of the user")
    lastname = A.text(doc="The last name of the user")
    password = A.text(doc="The password of the user")
    confirmationKey = A.text(doc="A random number generated to send to the user's email address")
    unconfirmedPassword = A.text(doc="Password is held here until confirmationKey is validated.")


class FileMeta(item.Item):
    """A file that has been uploaded."""
    schemaVersion = 1
    data = A.reference(doc="The FileData item that holds this file's data")
    thumbnail = A.reference(doc="The FileData item that holds the image thumbnail, if any")
    filename = A.text(doc="The basename of the file")
    mimeType = A.text(doc="The mime-type of the file")
    md5 = A.text(doc="The md5 hash of the file data")
    user = A.reference(doc="The User item who uploaded (owns?) the file")
    width = A.integer(doc="The width in pixels of the image, if an image")
    height = A.integer(doc="The height in pixels of the image, if an image")


class FileData(item.Item):
    schemaVersion = 1
    data = A.bytes(doc="The bytes in the file")

    def __repr__(self):
        return '<FileData @%x>' % (id(self),)


class Channel(item.Item):
    schemaVersion = 1
    name = A.text(doc="Name of the channel")
    topic = A.text(doc="What the channel topic is")
    topicAuthor = A.text(doc="Who set the topic")
    topicTime = A.timestamp(doc="When the topic was set")
    background = A.reference(doc="Image for the background of the channel map")
    gameTime = A.text(doc="A representation of the time in the game session")
    scale100px = A.point4decimal(doc="Distance in meters of 100 map px @ 100% zoom")
