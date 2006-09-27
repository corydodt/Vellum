from twisted.python.util import sibpath

from nevow import loaders, athena

class TabsElement(athena.LiveElement):
    docFactory = loaders.xmlstr(
"""<span xmlns:n="http://nevow.com/ns/nevow/0.1"
xmlns:athena="http://divmod.org/ns/athena/0.7"
n:render="liveElement"
class="tabsElement">
    <div class="handles" />
    <div class="panes" />
</span>
""")
    jsClass = u"Tabby.TabsElement"
    widgetArgs = None

    def addTab(self, id, label):
        return self.callRemote('addTab', id, label)

    def setInitialArguments(self, *a, **kw):
        assert len(kw) == 0, "Cannot pass keyword arguments to a Widget"
        self.widgetArgs = a


    def getInitialArguments(self):
        args = ()
        if self.widgetArgs is not None:
            args = self.widgetArgs

        return args

