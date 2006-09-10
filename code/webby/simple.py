# vi:ft=python
from twisted.application import service, internet
from twisted.python.util import sibpath

from nevow import tags as T, rend, loaders, appserver, athena, url

class SimpleFrag(athena.LiveFragment):
    docFactory = loaders.xmlstr("""
    <p xmlns:athena="http://divmod.org/ns/athena/0.7" xmlns:n="http://nevow.com/ns/nevow/0.1" n:render="liveFragment"><athena:handler event="onkeyup" handler="clicked" /><input class="chatentry"/></p>
""")

    jsClass = u"Simple.SimpleFrag"

    def typed(self, value):
        print '________________', value
    athena.expose(typed)

RESOURCE = lambda f: sibpath(__file__, f)

class SimpleRoot(rend.Page):
    addSlash = True
    def child__(self, ctx, ):
        return SimplePage()

    def renderHTTP(self, ctx):
        return url.root.child("_")


class SimplePage(athena.LivePage):
    addSlash = 1

    docFactory = loaders.stan(T.html[
        T.head[
            T.title["Simple"],
            T.invisible(render=T.directive("liveglue")),
        ],
        T.body[
            T.div(render=T.directive("simpleFrag")),
            T.p(render=T.directive("debug")),
        ]])
    def render_debug(self, ctx, data):
        f = athena.IntrospectionFragment()
        f.page = self
        return f
    def render_simpleFrag(self, ctx, data):
        f = SimpleFrag()
        f.page = self
        return f
    def __init__(self, *a, **kw):
        super(SimplePage, self).__init__(*a, **kw)
        self.jsModules.mapping[u'Simple'] = RESOURCE('simple.js')



application = service.Application('Simple')
svc = internet.TCPServer(8080, appserver.NevowSite(SimpleRoot()))
svc.setServiceParent(application)
