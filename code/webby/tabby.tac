# vi:ft=python
from twisted.application import service, internet
from twisted.python.util import sibpath

from nevow import appserver, rend, loaders, tags as t, url, athena

RESOURCE = lambda f: sibpath(__file__, f)

from tabs import TabsFragment


class TabbedPage(athena.LivePage):
    addSlash = True
    docFactory = loaders.xmlfile(RESOURCE('tabby.xhtml'))
    def render_tabs(self, ctx, _):
        tf = TabsFragment()
        tf.page = self
        return ctx.tag[tf]

    def __init__(self, *a, **kw):
        super(TabbedPage, self).__init__(*a, **kw)
        self.jsModules.mapping[u'Tabby'] = RESOURCE('tabby.js')


class WVRoot(rend.Page):
    addSlash = True
    def child__(self, ctx, ):
        return TabbedPage()

    def child_css(self, ctx, ):
        return static.File(RESOURCE('webby.css'))

    def renderHTTP(self, ctx):
        return url.root.child("_")


ROOT = WVRoot()

application = service.Application('WebbyVellum')
websvc = internet.TCPServer(8080, appserver.NevowSite(ROOT))
websvc.setServiceParent(application)

