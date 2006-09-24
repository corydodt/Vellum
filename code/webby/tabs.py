from twisted.python.util import sibpath

from nevow import loaders, athena

RESOURCE = lambda f: sibpath(__file__, f)

class TabsFragment(athena.LiveFragment):
    docFactory = loaders.xmlstr(
"""<span xmlns:n="http://nevow.com/ns/nevow/0.1"
xmlns:athena="http://divmod.org/ns/athena/0.7"
n:render="liveFragment"
class="tabsFragment">
    <div class="handles" />
    <div class="panes" />
</span>
""")
    jsClass = u"Tabby.TabsFragment"
    widgetArgs = None

    def addTab(self, id, label):
        self.callRemote('addTab', id, label)

    def setInitialArguments(self, *a, **kw):
        assert len(kw) == 0, "Cannot pass keyword arguments to a Widget"
        self.widgetArgs = a


    def getInitialArguments(self):
        args = ()
        if self.widgetArgs is not None:
            args = self.widgetArgs

        return args

