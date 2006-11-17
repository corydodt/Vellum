from twisted import plugin

from axiom.scripts import axiomatic
from axiom import iaxiom

from webby.data import DataService, appdata, User
from webby import ircserver, web, theGlobal

STOREDIR = appdata.child('glassvellum.axiom')

class Install(axiomatic.AxiomaticCommand):
    """Create the initial Vellum database, and attach all services."""

    longdesc = __doc__

    description = __doc__

    name = "install"

    optParameters = [
        ('smtpFrom',   'f', u'vellum@vellum.berlios.de',
         'The email address to use when sending emails.'),
        ('smtpServer', 's', u'smtp.comcast.net',
         'The outgoing SMTP server.  Email will be sent through here.'),
        ]

    optFlags = [('demodata', None, 'Put some sample data in the database.')]

    def postOptions(self):
        self.parent['dbdir'] = STOREDIR
        s = self.parent.getStore()
        svc = s.findOrCreate(DataService,
                             smtpFrom=self['smtpFrom'],
                             smtpServer=self['smtpServer'],
                             )
        svc.installOn(s)

        s.findOrCreate(ircserver.IRCService, portNumber=6667).installOn(s)
        s.findOrCreate(web.WebService, portNumber=8080).installOn(s)

        if self['demodata']:
            user = User(store=s,
                        email=u'a@b.c',
                        nick=u'MFen',
                        password=u'abc'
                        )
'''
        map = Map(store=s, 
                  name=u"The Gnoll Huddle", 
                  path=s.filesdir.child('gnoll-huddle.jpg'),
                  scale100px=Decimal("30.48"))
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
'''

class StartVellum(axiomatic.Start, axiomatic.AxiomaticCommand):
    """Start Vellum, using $HOME/.vellum or equivalent to find the store"""
    longdesc = __doc__

    description = __doc__

    name = "start-vellum"

    def postOptions(self):
        self.parent['dbdir'] = STOREDIR.path

        theGlobal['database'] = self.parent.getStore()

        return super(StartVellum, self).postOptions()

