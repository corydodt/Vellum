import warnings; warnings.filterwarnings('ignore')

from twisted.application import service, internet
from twisted.spread import pb

from nevow import static, appserver


from vellum.server import PBPORT, HTTPPORT
from vellum.server.pb import Gameness
from vellum.server.irc import VellumTalkFactory

webroot = static.File('.')

application = service.Application('SeeFantasy')

ircsvc = internet.TCPClient('irc.freenode.net', 6667, 
                            VellumTalkFactory('#vellum'))

pbsvc = internet.TCPServer(PBPORT, pb.PBServerFactory(Gameness()))

httpsvc = internet.TCPServer(HTTPPORT, appserver.NevowSite(webroot))

ircsvc.setServiceParent(application)
pbsvc.setServiceParent(application)
httpsvc.setServiceParent(application)

