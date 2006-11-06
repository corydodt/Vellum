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

class DataService(service.MultiService):
    def __init__(self, createData, *a, **kw):
        service.MultiService.__init__(self, *a, **kw)
        self.createData = createData

    def startService(self):
        self.store = store.Store(appdata.child('glassvellum.axiom'))
        log.msg("Starting service %r in %s" % (self, appdata,))

        # TODO - substores are going to be kept in zipfiles, which can
        # be opened from anywhere you want and used as substores from
        # the temp directory where they will be unpacked.
        # Until that is implemented, this is hardcoded.
        self.substore = store.Store(appdata.child('gnoll.axiom'))

        if self.createData:
            self.createInitialData()
            log.msg("Created initial database.")

    def createInitialData(self):
        s = self.substore
        map = Map(store=s, 
                  name=u"The Gnoll Huddle", 
                  path=s.filesdir.child('gnoll-huddle.jpg'),
                  scale100px="30.48")
        Character(store=s,
                  name=u"Shara",
                  path=s.filesdir.child('shara-kw.png'),
                  top=900, left=1000, scale=Decimal("1.0"),
                  ).installOn(map)
        Character(store=s,
                  name=u"Halbren",
                  path=s.filesdir.child('halbren.png'),
                  top=1000, left=1020, scale=Decimal("1.0"),
                  ).installOn(map)
        Character(store=s, 
                  name=u"Crom Grumdalsen", 
                  path=s.filesdir.child('crom.png'),
                  scale=Decimal("1.0"),
                  ).installOn(map)

"""
    - TODO
        name: The Gnoll Huddle (obscurement)
        uri: images/gnoll-huddle_obm.png
        type: mask/obscurement
"""

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
    schemaVersion = 1
    email = A.text("The username used to log in", allowNone=False)
    nick = A.text("The default nick to use in IRC")
    firstname = A.text()
    lastname = A.text()
    password = A.text()
