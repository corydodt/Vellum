"""The core web server on which the Vellum application is based."""
from zope.interface import implements
 
from nevow import inevow, rend, tags, guard, loaders, static, url, appserver, static

from axiom import attributes as A

from twisted.cred import portal, checkers, credentials, error
from twisted.python.util import sibpath
from twisted.python import log

from webby.ircweb import IRCPage 
from webby.signup import SignupPage
from webby import theGlobal, data, gmtools


RESOURCE = lambda f: sibpath(__file__, f)


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


def noLogout():
    return None

class FileTree(rend.Page):
    """The /files url.

    URLs of the form /files/<md5> will return the file with that md5sum for
    the current user.  If /thumb is appended, return the thumbnail image
    instead.
    """
    def __init__(self, user, *a, **kw):
        rend.Page.__init__(self, *a, **kw)
        self.user = user

    def locateChild(self, ctx, segs):
        md5 = segs[0]
        db = theGlobal["dataService"].store
        _filter = A.AND(data.File.md5==unicode(md5), data.File.user==self.user)
        fileitem = db.findFirst(data.File, _filter)
        if fileitem is None:
            return None, ()
        if segs[1] == 'thumb':
            return static.Data(fileitem.thumbnail, 'image/png'), ()
        else:
            return static.Data(fileitem.data, fileitem.mimeType), ()

class StaticRoot(rend.Page):
    """
    Adds child nodes for things common to anonymous and logged-in root
    resources.

    Must be subclassed as it has no docFactory of its own.
    """
    addSlash = True  # yeah, we really do need this, otherwise 404 on /
    def child_css(self, ctx, ):
        return static.File(RESOURCE('webby.css'))

    def child_tabs_css(self, ctx, ):
        return static.File(RESOURCE('tabs.css'))

    def child_signup(self, ctx, ):
        return SignupPage()

    def child_images(self, ctx, ):
        return static.File(RESOURCE('images'))
 
class VellumRealm:
    implements(portal.IRealm)
    class LoginPage(StaticRoot):
        """Page which asks for username/password."""
        addSlash = True
        docFactory = loaders.xmlfile(RESOURCE('login.xhtml'))
     
        def render_form(self, ctx, data):
            req = inevow.IRequest(ctx)
            if 'login-failure' in req.args:
                ctx.tag.fillSlots('loginStatus', ctx.tag.onePattern('unauthorized'))
            else:
                ctx.tag.fillSlots('loginStatus', [])

            ctx.tag.fillSlots('action', guard.LOGIN_AVATAR)
            return ctx.tag
     
        def logout(self):
            print "Bye"
 
    class LoggedInRoot(StaticRoot):
        """
        This root will be available when the user has credentials (is
        logged in).
        """
        def __init__(self, user, *a, **kw):
            StaticRoot.__init__(self, *a, **kw)
            self.user = user

        def child_files(self, ctx, ):
            return FileTree(self.user)

        def child_upload(self, ctx, ):
            return gmtools.UploadPage(self.user)

        def child_game(self, ctx, ):
            inevow.ISession(ctx).user = self.user
            return IRCPage()

        def renderHTTP(self, ctx):
            return url.root.child("game")

        def logout(self):
            """Does nothing right now."""

    def requestAvatar(self, avatarId, mind, *interfaces):
        for iface in interfaces:
            if iface is inevow.IResource:
                # do web stuff
                if avatarId is checkers.ANONYMOUS:
                    resc = VellumRealm.LoginPage()
                    resc.realm = self
                    return (inevow.IResource, resc, noLogout)
                else:
                    resc = VellumRealm.LoggedInRoot(avatarId)
                    resc.realm = self
                    return (inevow.IResource, resc, resc.logout)
 
        raise NotImplementedError("Can't support that interface.")
 
class AxiomEmailChecker(object):
    """
    This is also pasted over in webby.ircserver as AxiomNickChecker.
    """
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = credentials.IUsernamePassword,

    def requestAvatarId(self, credentials):
        store = theGlobal['dataService'].store

        username = unicode(credentials.username)
        password = unicode(credentials.password)

        u = store.findFirst(data.User, data.User.email==username)

        # Note: If the account has not been confirmed from the email
        # address, u.password will be None.
        if u is not None and u.password == password:
            # clear unconfirmedPassword here.  This is needed if either of the
            # following occurs:
            # a) user visits the forgot password page but subsequently
            # remembers the original password
            # b) malicious user visits the forgot password page but can't
            # confirm the new password, and the real user logs in at some
            # point.
            u.unconfirmedPassword = None
            return u

        raise error.UnauthorizedLogin()

def guardedRoot():
    realm = VellumRealm()
    port = portal.Portal(realm)

    myChecker = AxiomEmailChecker()

    port.registerChecker(checkers.AllowAnonymousAccess(), credentials.IAnonymous)
    port.registerChecker(myChecker)

    res = guard.SessionWrapper(port)
    
    return res

