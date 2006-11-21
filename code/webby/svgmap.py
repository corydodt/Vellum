"""The SVG Map"""

from twisted.python.util import sibpath

from nevow import athena, loaders

RESOURCE = lambda f: sibpath(__file__, f)

class MapWidget(athena.LiveElement):
    jsClass = u'SVGMap.MapWidget'
    docFactory = loaders.xmlfile(RESOURCE('elements/SVGMap'))
