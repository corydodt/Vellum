from nevow import athena
from nevow.livetrial import testcase

from axiom import store

from webby import svgmap, theGlobal, data, ircweb
from webby.test.livetest_ircweb import testUser

# define our in-memory test store
testStore = store.Store()
testFileData = data.FileData(store=testStore,
data=(
"""iVBORwoaCgAAAA1JSERSAAAAZAAAAGQIAgAAAP+AAgMAAAAJcEhZcwAACxMAAAsTAQCanBgAAAAH
dElNRQfWCx0HNiv9/5VxAAAACHRFWHRDb21tZW50APbMlr8AAACfSURBVHja7dAxAQAACAMgtX/n
WcHPByLQSYqbUSBLlixZsmQpkCVLlixZshTIkiVLlixZCmTJkiVLliwFsmTJkiVLlgJZsmTJkiVL
gSxZsmTJkqVAlixZsmTJUiBLlixZsmQpkCVLlixZshTIkiVLlixZCmTJkiVLliwFsmTJkiVLlgJZ
smTJkiVLgSxZsmTJkqVAlixZsmTJUiBL1rcFz/EDxVmyyQcAAAAASUVORK5CYII="""
).decode('base64'))
testFileMeta = data.FileMeta(store=testStore, 
        data=testFileData,
        filename=u'white100.png',
        mimeType=u'image/png',
        md5=u'c2d8ac97a07cbf785d2e4d7dbf578d2c',
        width=100,
        height=100)

theGlobal['database'] = testStore

class TestMapWidget(testcase.TestCase):
    jsClass = u'SVGMap.Tests.TestMapWidget'
    def newMapWidgetInContainer(self):
        """
        Return a new SVGMap
        """
        enc = ircweb.IRCContainer(None, testUser)
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
        bgi = svgmap.BackgroundImage(testFileMeta)
        bgi.setFragmentParent(self)
        return bgi

    athena.expose(requestSetMapBackground)
