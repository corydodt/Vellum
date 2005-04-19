from twisted.application import service, internet
from twisted.spread import pb, util
from nevow import static, appserver


from vellum.server import PBPORT, HTTPPORT
from vellum.server.pb import Gameness

webroot = static.File('.')

application = service.Application('SeeFantasy')
pbsvc = internet.TCPServer(PBPORT, pb.PBServerFactory(Gameness()))
httpsvc = internet.TCPServer(HTTPPORT, appserver.NevowSite(webroot))
pbsvc.setServiceParent(application)
httpsvc.setServiceParent(application)

