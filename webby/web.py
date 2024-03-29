"""The core web server on which the Vellum application is based."""
from zope.interface import implements
 
from nevow import (inevow, rend, tags, guard, loaders, static, url, appserver,
        static, vhost)

from axiom import attributes as A, item, userbase

from xmantissa import websession

from twisted.cred import portal, checkers, credentials, error
from twisted.python.util import sibpath
from twisted.python import log

from webby.ircweb import IRCPage 
from webby.signup import SignupPage
from webby import theGlobal, data, gmtools, util, RESOURCE



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
        db = theGlobal["database"]
        FM = data.FileMeta
        # for now, everyone gets access to everyone else's files
        # TODO - implement permissions on files?
        _filter = A.AND(FM.md5==unicode(md5))
        fileitem = db.findFirst(FM, _filter)
        if fileitem is None:
            return None, ()
        if len(segs) > 1 and segs[1] == 'thumb':
            return static.Data(fileitem.thumbnail.data, 'image/png'), ()
        else:
            mimeType = fileitem.mimeType.encode('utf-8')
            return static.Data(fileitem.data.data, mimeType), ()

class StaticRoot(rend.Page):
    """
    Adds child nodes for things common to anonymous and logged-in root
    resources.

    Must be subclassed as it has no docFactory of its own.
    """
    addSlash = True  # yeah, we really do need this, otherwise 404 on /
    def child_static(self, ctx):
        return static.File(RESOURCE('static'))

    def child_signup(self, ctx, ):
        return SignupPage()

class VellumRealm:
    """
    TODO - combine this with VellumIRCRealm.  Look at requestAvatar and see
    what interfaces the irc realm looks for.  Something with the portal, too.
    """

    implements(portal.IRealm)
    class LoginPage(StaticRoot):
        """Page which asks for username/password."""
        addSlash = True
        docFactory = loaders.xmlfile(RESOURCE('templates/login.xhtml'))

        def child_game(self, ctx,):
            """Redirect to the login page when you attempt to return to /game"""
            return url.root.child('')
     
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
    credentialInterfaces = (credentials.IUsernamePassword, 
            userbase.IPreauthCredentials)

    def requestAvatarId(self, creds):
        store = theGlobal['database']

        username = unicode(creds.username)

        u = store.findFirst(data.User, data.User.email==username)

        if u is not None:
            if userbase.IPreauthCredentials.providedBy(creds):
                return u

            elif credentials.IUsernamePassword.providedBy(creds):
                password = unicode(creds.password)

                # Note: If the account has not been confirmed from the email
                # address, u.password will be None.
                if u is not None and u.password == password:
                    # clear unconfirmedPassword here.  This is needed if
                    # either of the following occurs:
                    # a) user visits the forgot password page but subsequently
                    # remembers the original password
                    # b) malicious user visits the forgot password page but
                    # can't confirm the new password, and the real user logs
                    # in at some point.
                    u.unconfirmedPassword = None
                    return u

        raise error.UnauthorizedLogin()

def guardedRoot(db):
    realm = VellumRealm()
    port = portal.Portal(realm)

    myChecker = AxiomEmailChecker()

    port.registerChecker(checkers.AllowAnonymousAccess(), credentials.IAnonymous)
    port.registerChecker(myChecker)

    res = websession.PersistentSessionWrapper(db, port)
    
    return res

class VhostFakeRoot:
    """
    I am a wrapper to be used at site root when you want to combine 
    vhost.VHostMonsterResource with nevow.guard. If you are using guard, you 
    will pass me a guard.SessionWrapper resource.
    """
    implements(inevow.IResource)
    def __init__(self, wrapped):
        self.wrapped = wrapped
    
    def renderHTTP(self, ctx):
        return self.wrapped.renderHTTP(ctx)
        
    def locateChild(self, ctx, segments):
        """Returns a VHostMonster if the first segment is "vhost". Otherwise
        delegates to the wrapped resource."""
        if segments[0] == "VHOST":
            return vhost.VHostMonsterResource(), segments[1:]
        else:
            return self.wrapped.locateChild(ctx, segments)

class WebService(item.Item, util.AxiomTCPServerMixin):
    @staticmethod
    def factory():
        return STFUSite(VhostFakeRoot(guardedRoot(theGlobal['database'])))

    schemaVersion = 1
    portNumber = A.integer(doc="The port on which to run.")
    interface = A.text(
          doc="Dotted-decimal interface to run on, '' for all interfaces", 
          default=u'')

    port = A.inmemory()
    parent = A.inmemory()
    running = A.inmemory()

