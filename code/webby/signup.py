"""Concept (not code) borrowed unrepentantly from Divmod Mantissa."""
import rfc822
from email.MIMEText import MIMEText
import random

from twisted.python.util import sibpath
from twisted.mail import smtp

from nevow import athena, loaders, url, flat, inevow

from webby import theGlobal, data

RESOURCE = lambda f: sibpath(__file__, f)

class Signup(athena.LiveElement):
    docFactory = loaders.xmlfile(RESOURCE('elements/Signup'))
    jsClass = u'WebbyVellum.Signup'
    def __init__(self, pageURL, *a, **kw):
        super(Signup, self).__init__(*a, **kw)
        self.pageURL = pageURL

    def processSignup(self, email, password):
        # let's make this key very unique.
        key_a = unicode(random.random() * 10000000)
        key_b = unicode(random.random() * 10000000)
        key = key_a + key_b 
        store = theGlobal['dataService'].store
        u = store.findFirst(data.User, data.User.email==email)

        if u is None:
            u = data.User(store=store, 
                          email=email,
                          password=None,
                          unconfirmedPassword=password,
                          confirmationKey=key)
        else:
            u.unconfirmedPassword = password
            u.confirmationKey = key

        link = self.pageURL + '?confirm=%s' % (key,)

        d = sendEmail(email, "Confirm Vellum Signup", ## {{{
"""
You signed up to use Vellum, I think.

Confirm your signup on the Vellum website by clicking on the following link:
%s
""" % (link,)) ## }}}

        d.addCallback(lambda response: unicode(response))

        def _didntSendEmail(failure):
            """Remove the new user object if we can't even send the email"""
            u.deleteFromStore()
            return failure

        d.addErrback(_didntSendEmail)

        return d

    athena.expose(processSignup)


class SignupPage(athena.LivePage):
    addSlash = 1
    docFactory = loaders.xmlfile(RESOURCE('signup.xhtml'))

    def render_signup(self, ctx, data):
        pageURL = flat.flatten(url.URL.fromContext(ctx))
        signup = Signup(pageURL)
        signup.setFragmentParent(self)
        return signup

    def renderHTTP(self, ctx):
        """
        Check for a confirmation being used from the email link.

        If the user is confirming a login, move the password from
        unconfirmedPassword into password, thus enabling the account.
        """
        req = inevow.IRequest(ctx)
        confirm = req.args.get('confirm', None) 
        if confirm is not None:
            confirm = unicode(confirm[0])
            store = theGlobal['dataService'].store
            u = store.findFirst(data.User, data.User.confirmationKey==confirm)
            if u is not None:
                u.password = u.unconfirmedPassword
                u.unconfirmedPassword = None
                req.args.clear()
                self.docFactory = loaders.xmlfile(RESOURCE('confirmed.xhtml'))
            else:
                self.docFactory = loaders.stan(['Could not confirm that account.'])
        return super(SignupPage, self).renderHTTP(ctx)



def sendEmail(toAddr, subject, body):
    """Send email, return Deferred of result."""
    msg = MIMEText(body)
    msg["To"] = toAddr
    msg["From"] = theGlobal['smtpFrom']
    msg["Subject"] = subject or "Message from Vellum"
    msg["Date"] = rfc822.formatdate()
    d = smtp.sendmail(theGlobal['smtpServer'], theGlobal['smtpFrom'], [toAddr], 
            msg.as_string())
    return d