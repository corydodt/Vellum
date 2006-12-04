import sys, os

from twisted.python.filepath import FilePath

from axiom.scripts import axiomatic
from axiom import iaxiom

from epsilon.extime import Time

from webby.data import DataService, User, Channel
from webby import ircserver, web, theGlobal

if sys.platform == 'win32':
    appdata = FilePath(os.path.join(os.environ['APPDATA'], 'Vellum'))
else:
    appdata = FilePath(os.path.join(os.environ['HOME'], '.vellum'))

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
        def _txn():
            svc = s.findOrCreate(DataService,
                                 smtpFrom=self['smtpFrom'],
                                 smtpServer=self['smtpServer'],
                                 )
            svc.installOn(s)

            s.findOrCreate(ircserver.IRCService, 
                    portNumber=6667,
                    interface=u'127.0.0.1').installOn(s)

            s.findOrCreate(web.WebService, portNumber=8080,).installOn(s)

            if self['demodata']:
                s.findOrCreate(User, email=u'a@b.c', nick=u'MFen', 
                        password=u'abc')
                s.findOrCreate(Channel, name=u'#vellum', 
                        topic=u'Welcome to #vellum',
                        topicAuthor=u'VellumTalk', 
                        topicTime=Time())
        s.transact(_txn)

'''
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

