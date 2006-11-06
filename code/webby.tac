# vi:ft=python
from twisted.application import service, internet
from twisted.python import log

from nevow import appserver

from webby.ajazz import WVRoot
from webby.ircserver import theIRCFactory
from webby.data import DataService

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

datasvc = DataService(createData=False)
datasvc.setServiceParent(application)

ROOT = WVRoot()

websvc = internet.TCPServer(8080, STFUSite(ROOT))
websvc.setServiceParent(application)

ircsvc = internet.TCPServer(6667, theIRCFactory)
ircsvc.setServiceParent(application)
