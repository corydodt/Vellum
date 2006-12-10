"""The SVG Map"""
from twisted.python.util import sibpath

from zope.interface import implements

from nevow import athena, loaders, tags as T

from webby import theGlobal, data, iwebby, RESOURCE

class BackgroundImage(athena.LiveElement):
    ## jsClass = u'SVGMap.BackgroundImage'
    docFactory = loaders.xmlfile(RESOURCE('elements/BackgroundImage'))
    def __init__(self, fileitem, *a, **kw):
        super(BackgroundImage, self).__init__(*a, **kw)
        self.fileitem = fileitem

    def imageLiveElement(self, req, tag):
        # FIXME - don't hardcode href netloc
        href = u'/files/%s' % (self.fileitem.md5,)
        tag.fillSlots('width', self.fileitem.width)
        tag.fillSlots('height', self.fileitem.height)
        tag.fillSlots('href', href)
        return tag(render=T.directive("liveElement"))

    athena.renderer(imageLiveElement)

class MapWidget(athena.LiveElement):
    implements(iwebby.IMapWidget)
    jsClass = u'SVGMap.MapWidget'
    docFactory = loaders.xmlfile(RESOURCE('elements/MapWidget'))

    def setMapBackground(self, md5key):
        db = theGlobal['database']
        # TODO - assert that this really is an image
        filemeta = db.findFirst(data.FileMeta, data.FileMeta.md5 == unicode(md5key))
        image = BackgroundImage(filemeta)
        image.setFragmentParent(self)
        return self.callRemote("setMapBackground", image)
