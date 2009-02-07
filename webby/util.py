import random

from twisted.internet import defer

from nevow import tags as T, flat, athena

from axiom import item, attributes as A

from twisted.application.internet import TCPServer
from twisted.application.service import IService
from twisted.internet import reactor

def flattenMessageString(st):
    """Return a string suitable for serializing over to a tab pane."""
    span = T.span(xmlns="http://www.w3.org/1999/xhtml")
    for line in st.splitlines():
        span[line, T.br]
    return unicode(flat.flatten(span))

class RenderWaitLiveElement(athena.LiveElement):
    """
    callRemote calls will be queued until the widget is rendered, then all
    calls will be made at once.
    """
    def __init__(self, *a, **kw):
        super(RenderWaitLiveElement, self).__init__(*a, **kw)
        self._callRemoteQueue = []

    def callRemote(self, *a, **kw):
        # queue calls pre-render.
        if getattr(self, '_athenaID', None) is None:
            d = defer.Deferred()
            self._callRemoteQueue.append([d, a, kw])
            return d
        else:
           return super(RenderWaitLiveElement, self).callRemote(*a, **kw)


    def rend(self, *a, **kw):
        r = super(RenderWaitLiveElement, self).rend(*a, **kw)

        while len(self._callRemoteQueue) > 0:
            d1, qa, qkw = self._callRemoteQueue.pop()
            d2 = super(RenderWaitLiveElement, self).callRemote(*qa, **qkw)

            d2.addCallback(d1.callback)

        return r


def label():
    """Make a pretty darn unique key."""
    key_a = unicode(random.random() * 10000000)
    key_b = unicode(random.random() * 10000000)
    return key_a + key_b 

class AxiomTCPServerMixin(TCPServer):
    powerupInterfaces = (IService,)
    def privilegedStartService(self):
        pass

    def startService(self):
        self.port = reactor.listenTCP(self.portNumber, self.factory(),
                interface=(self.interface or ''))
