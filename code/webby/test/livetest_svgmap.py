from nevow import athena
from nevow.livetrial import testcase

from webby import svgmap, data, ircweb
from webby.test.teststore import testUser, testFileMeta, cleanStore

class TestMapWidget(testcase.TestCase):
    jsClass = u'SVGMap.Tests.TestMapWidget'
    def newMapWidgetInContainer(self):
        """
        Return a new SVGMap
        """
        enc = ircweb.IRCContainer(None, testUser(cleanStore()))
        enc.setFragmentParent(self)
        return enc

    athena.expose(newMapWidgetInContainer)

    def newMapWidget(self):
        """
        Return a new SVGMap
        """
        mapw = svgmap.MapWidget()
        mapw.setFragmentParent(self)
        return mapw

    athena.expose(newMapWidget)

    def requestSetMapBackground(self):
        """
        Return a new BackgroundImage object 
        """
        bgi = svgmap.BackgroundImage(testFileMeta(cleanStore()))
        bgi.setFragmentParent(self)
        return bgi

    athena.expose(requestSetMapBackground)
