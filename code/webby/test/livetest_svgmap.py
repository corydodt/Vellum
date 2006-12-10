from nevow import athena
from nevow.livetrial import testcase

from webby import svgmap, data, ircweb, obscurement
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
        st = cleanStore()
        chan = data.Channel(store=st, name=u'#foo')
        mapw = svgmap.MapWidget(chan)
        mapw.setFragmentParent(self)
        return mapw

    athena.expose(newMapWidget)

    def requestSetMapBackground(self):
        """
        Return a new BackgroundImage object 
        """
        st = cleanStore()
        chan = data.Channel(store=st, name=u'#foo')
        fileitem = testFileMeta(st)
        odata = data.FileData(store=st, data=obscurement.newBlackImage(100,100))
        obsc = data.FileMeta(store=st,
                data=odata,
                filename=u'#foo_obscurement.png',
                mimeType=u'image/png',
                md5=u'316ca7b4c921a204797dfbb70becfef9',
                width=100,
                height=100,
                )
        chan.background = fileitem
        chan.obscurement = obsc
        bgi = svgmap.BackgroundImage(chan)
        bgi.setFragmentParent(self)
        return bgi

    athena.expose(requestSetMapBackground)
