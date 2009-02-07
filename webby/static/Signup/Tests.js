// import Nevow.Athena.Test
// import Divmod

Signup.Tests.TestSignup = Nevow.Athena.Test.TestCase.subclass("Signup.Tests.TestSignup");
Signup.Tests.TestSignup.methods( // {{{
    function test_initialize(self) { // {{{
        var d = self.setUp();
        d.addCallback(function _(signup) {
            var email = signup.node.email;
            var password1 = signup.node.password1;
            var password2 = signup.node.password2;
            var message = signup.firstNodeByAttribute('class', 'message');
            self.assertEqual(email.value, '');
            self.assertEqual(password1.value, '');
            self.assertEqual(password2.value, '');
            self.assertEqual(message.innerHTML, '');
        });
        return d
    }, // }}}

    function test_submit(self) { // {{{
        var d = self.setUp();
        d.addCallback(function _(signup) {
            var email = signup.firstNodeByAttribute('name', 'email');
            var password1 = signup.firstNodeByAttribute('name', 'password1');
            var password2 = signup.firstNodeByAttribute('name', 'password2');
            var message = signup.firstNodeByAttribute('class', 'message');
            var ev = new MockEvent(signup.node);
            // submit with all fields blank
            signup.submit(ev);
            self.assertEqual(message.innerHTML, 
                    'Please fill in your email address.');
            // submit with password1 or password2 blank
            email.value = 'foo@sample.com';
            signup.submit(ev);
            self.assertEqual(message.innerHTML, 
                    'Please fill in your new password twice.');

            message.innerHTML = '';

            password1.value = 'ohno';
            signup.submit(ev);
            self.assertEqual(message.innerHTML, 
                    'Please fill in your new password twice.');
            // submit with password1 != password2
            password2.value = 'ohmy';
            signup.submit(ev);
            self.assertEqual(message.innerHTML, 
                    "Passwords don't match! Try again.");
            // submit correctly
            password2.value = 'ohno';
            var d2 = signup.submit(ev);
            d2.addCallback(function _(ignored) {
                self.assertEqual(message.innerHTML,
                    "An email has been sent to the above address."); 
            });

            // submit with a bad email address. this will make the call
            // errback due to the test infrastructure, but has no such effect
            // in the production environment.  FIXME, maybe.
            email.value = 'foo_sample.com';
            var d3 = signup.submit(ev);
            d3.addCallback(function _(ignored) {
                self.assert(0, "This should have called errback.");
            });
            d3.addErrback(function _(ignored) {
                self.assertEqual(message.innerHTML, 
                        'An error occurred signing you up.');
            });
            return Divmod.Defer.DeferredList([d2, d3], false, true);
        });
        return d;
    }, // }}}

    function setUp(self) { // {{{
        var d = self.callRemote("newSignup");
        d.addCallback(
            function _(wi) { return self.addChildWidgetFromWidgetInfo(wi); }
            );
        return d;
    } // }}}
); // }}}


