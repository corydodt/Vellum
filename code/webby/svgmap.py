"""The SVG Map"""

from twisted.python.util import sibpath

from zope.interface import implements

from nevow import athena, loaders

RESOURCE = lambda f: sibpath(__file__, f)

class MapWidget(athena.LiveElement):
    implements(iwebby.IMapWidget)
    jsClass = u'SVGMap.MapWidget'
    docFactory = loaders.xmlfile(RESOURCE('elements/SVGMap'))

    def setBackgroundMap(self, md5key):
        pass
