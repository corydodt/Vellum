"""The SVG Map"""
from twisted.python.util import sibpath

from zope.interface import implements

from nevow import athena, loaders, tags as T

from webby import iwebby, RESOURCE

class BackgroundImage(athena.LiveElement):
    ## jsClass = u'SVGMap.BackgroundImage'
    docFactory = loaders.xmlfile(RESOURCE('elements/BackgroundImage'))
    def __init__(self, channel, *a, **kw):
        super(BackgroundImage, self).__init__(*a, **kw)
        self.channel = channel

    def imageLiveElement(self, req, tag):
        # FIXME - don't hardcode href netloc
        ch = self.channel
        href = u'/files/%s' % (ch.background.md5,)
        obscurementHref = u'/files/%s' % (ch.obscurement.md5,)
        tag.fillSlots('width', ch.background.width)
        tag.fillSlots('height', ch.background.height)
        tag.fillSlots('href', href)
        tag.fillSlots('obscurementHref', obscurementHref)
        return tag(render=T.directive("liveElement"))

    athena.renderer(imageLiveElement)

class MapWidget(athena.LiveElement):
    implements(iwebby.IMapWidget)
    jsClass = u'SVGMap.MapWidget'
    docFactory = loaders.xmlfile(RESOURCE('elements/MapWidget'))
    def __init__(self, channel, chatEntry, *a, **kw):
        super(MapWidget, self).__init__(*a, **kw)
        self.channel = channel
        self.chatEntry = chatEntry

    def setMapBackgroundFromChannel(self):
        image = BackgroundImage(self.channel)
        image.setFragmentParent(self)
        return self.callRemote("setMapBackground", image)

    def sendCommand(self, command):
        return self.chatEntry.chatMessage(command)

    athena.expose(sendCommand)
