"""The core web server on which the Vellum application is based."""

from twisted.python.util import sibpath
from twisted.python import log

from nevow import static, rend, url, appserver

from webby.ircweb import IRCPage 
from webby.signup import SignupPage

RESOURCE = lambda f: sibpath(__file__, f)

class WVRoot(rend.Page):
    addSlash = True
    def child__(self, ctx, ):
        return IRCPage()

    def child_css(self, ctx, ):
        return static.File(RESOURCE('webby.css'))

    def child_tabs_css(self, ctx, ):
        return static.File(RESOURCE('tabs.css'))

    def child_signup(self, ctx, ):
        return SignupPage()

    def renderHTTP(self, ctx):
        return url.root.child("_")


class STFUSite(appserver.NevowSite):
    """Website with <80 column logging"""
    def log(self, request):
        uri = request.uri
        if len(uri) > 20:
            uri = '...' + uri[-17:]

        code = request.code
        if code != 200:
            code = '!%s!' % (code, )

        log.msg('%s %s' % (code, uri))

