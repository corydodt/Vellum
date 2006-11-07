# vi:ft=python
from twisted.application import service, internet
from twisted.python import log

from nevow import appserver

from webby.ajazz import WVRoot
from webby.ircserver import theIRCFactory
from webby.data import DataService
from webby import theGlobal

######### CONFIG
######### CONFIG
######### CONFIG
######### CONFIG

theGlobal['smtpFrom'] = 'vellum@vellum.berlios.de'

theGlobal['smtpServer'] = 'smtp.comcast.net'

createData = False

#########
#########
#########
#########

class STFUSite(appserver.NevowSite):
    """Website with <80 column logging"""
    def log(self, request):
        uri = request.uri
        if len(uri) > 20:
            uri = '...' + uri[-17:]

        code = request.code
        if code != 200:
            code = '!%s!' % (code, )

        log.msg('%s %s' % (code, uri))

application = service.Application('WebbyVellum')

datasvc = DataService(createData=createData)
datasvc.setServiceParent(application)
theGlobal['dataService'] = datasvc

ROOT = WVRoot()

websvc = internet.TCPServer(8080, STFUSite(ROOT))
websvc.setServiceParent(application)

ircsvc = internet.TCPServer(6667, theIRCFactory)
ircsvc.setServiceParent(application)

def databaseMessage():
    m = log.msg
    m("__")
    m("__")
    m("__ I have just created a demo database.  I will not do anything else.")
    m("__ Edit the .tac file and set createData = False to start up for real.")
    m("__")
    m("__")
    reactor.stop()

if createData:
    from twisted.internet import reactor
    reactor.addSystemEventTrigger('after', 'startup', databaseMessage)
