from twisted.application import service, internet
from twisted.spread import pb, util
from nevow import static, appserver


from net import PBPORT, HTTPPORT

map = '/grimcatch.jpg'

class Gameness(pb.Root):
    def remote_listAvailableFiles(self):
        return [{'uri': map, 
                 'name': 'grimcatch',
                 'type': 'map', # others: 'character', 'object', 'sound', 'text'
                 'md5': '6b8846cb4b4de9ad6bb7f3471c4bd23a',
                 },
                {'uri': '/shara-kw.png',
                 'name': 'shara',
                 'type': 'character',
                 'md5': '0865ea97c08cb3cb47e68312a48222cb',
                 'top': 200,
                 'left': 200,
                 },
                {'uri': '/halbren.png',
                 'name': 'halbren',
                 'type': 'character',
                 'md5': 'ee9d888024cf8456402eb3883995398a',
                 'top': 50,
                 'left': 50,
                 },
                ]
    # character and object: name, image_mode, top, left
    # sound: name, top, left
    # text: title, top, left


webroot = static.File('.')

application = service.Application('SeeFantasy')
pbsvc = internet.TCPServer(PBPORT, pb.PBServerFactory(Gameness()))
httpsvc = internet.TCPServer(HTTPPORT, appserver.NevowSite(webroot))
pbsvc.setServiceParent(application)
httpsvc.setServiceParent(application)
