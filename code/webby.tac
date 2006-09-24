# vi:ft=python
from twisted.application import service, internet
from nevow import appserver

from webby.ajazz import WVRoot
from webby.ircserver import theIRCFactory


ROOT = WVRoot()

application = service.Application('WebbyVellum')
websvc = internet.TCPServer(8080, appserver.NevowSite(ROOT))
websvc.setServiceParent(application)

ircsvc = internet.TCPServer(6667, theIRCFactory)
ircsvc.setServiceParent(application)

