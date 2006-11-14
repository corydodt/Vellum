"""Dynamic Tabs Element

Drop one of these TabsElement items on your athena.LivePage.

Supports callRemotes for:

    addTab(id, label, scrollback) -> create a new tab in the widget

    removeTab(id)

    setTabBody(id, content) -> append content to the tab having id.  The
                                content must be a single xhtml-namespaced node.

    show(id) -> bring tab id to the foreground.

"""
from twisted.python.util import sibpath

from nevow import loaders, athena

RESOURCE = lambda f: sibpath(__file__, f)

EMPTY = ()

class TabsElement(athena.LiveElement):
    docFactory = loaders.xmlfile(RESOURCE('elements/Tabs'))
    jsClass = u"Tabby.TabsElement"
    widgetArgs = EMPTY

    def addTab(self, id, label):
        return self.callRemote('addTab', id, label)

    def setTabBody(self, id, content):
        return self.callRemote('setTabBody', id, content)

    def removeTab(self, id):
        return self.callRemote('removeTab', id)

    def addInitialTab(self, id, label, content):
        """
        Specify a tab that will be sent in the initial arguments.
        Has no effect after the first time this widget gets rendered.
        """
        assert getattr(self, '_athenaID', None) is None, (
                "Cannot call this after the widget has rendered.")
        if self.widgetArgs is EMPTY:
            self.widgetArgs = []
        self.widgetArgs.append((id, label, content))

    def getInitialArguments(self):
        return self.widgetArgs

