from nevow import athena, loaders
from nevow.livetrial import testcase

from webby import tabs

class VerySimpleWidget(athena.LiveElement):
    docFactory = loaders.xmlstr(
'''<span xmlns:n="http://nevow.com/ns/nevow/0.1"
         n:render="liveElement"><b>Content</b></span>''')

class TestTabs(testcase.TestCase):
    jsClass = u'Tabby.Tests.TestTabs'
    def newTabWidget(self, *a):
        """Return a new tab widget"""
        w = tabs.TabsElement()
        w.setFragmentParent(self)
        w.setInitialArguments(*a)
        return w

    athena.expose(newTabWidget)

    def newTabWidgetContainingWidget(self, *a):
        """Return a new tab widget, whose initial content is a widget"""
        t = tabs.TabsElement()
        t.setFragmentParent(self)

        vsw = VerySimpleWidget()
        vsw.setFragmentParent(self)

        # the initialContent must be third argument, so
        # modify the positional args appropriately
        if len(a) == 0:
            a = ['woop', 'Woop']

        a = list(a)

        a.append(vsw)

        t.setInitialArguments(*a)
        return t

    athena.expose(newTabWidgetContainingWidget)

    def newVerySimpleWidget(self):
        """Return a new tab widget"""
        vsw = VerySimpleWidget()
        vsw.setFragmentParent(self)
        return vsw

    athena.expose(newVerySimpleWidget)

    def driveAddTabSetTab(self):
        """Make the s->c calls for the test_addTabSetTab nit.
        Calls addTab and then setTabBody remotely.
        """
        vsw = VerySimpleWidget()
        vsw.setFragmentParent(self)

        d = self.callRemote('addTab', u'y', u'y')

        def _added(ignored):
            return self.callRemote('setTabBody', u'y', vsw)

        d.addCallback(_added)

        return d

    athena.expose(driveAddTabSetTab)
