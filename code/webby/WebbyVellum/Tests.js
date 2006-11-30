// import Nevow.Athena.Test
// import Divmod

MockEvent = Divmod.Class.subclass('MockEvent');
MockEvent.methods( // {{{
    function __init__(self, node) { self.target = self.srcElement = node; },

    function stopPropagation(self) { /* */ },

    function preventDefault(self) { /* */ }
); // }}}


WebbyVellum.Tests.TestIRCContainer = Nevow.Athena.Test.TestCase.subclass("WebbyVellum.Tests.TestIRCContainer");
WebbyVellum.Tests.TestIRCContainer.methods( // {{{
    function test_initialize(self) {  // {{{
        var d = self.setUp();
        d.addCallback(function _(irc) {
            // check that subwidgets are present and supply the right methods
            var accountManager = irc.childWidgets[0];
            self.failIf(accountManager.onLogOnSubmit === undefined);
            var conv = irc.childWidgets[1];
            self.failIf(conv.appendToTab === undefined);
            var chat = irc.childWidgets[2];
            self.failIf(chat.submit === undefined);

            var chatentry = chat.firstNodeByAttribute('class', 'chatentry');

            // entry field should start empty
            self.assertEqual(chatentry.value, '');

            var fgtab = irc.firstNodeByAttribute('class', 'tab');

            // the server tab should be in the foreground
            self.assertEqual(fgtab.id, '**SERVER**');

            // the nick field should be populated.
            self.assertEqual(accountManager.node.nick.value, 'woot');

            // TODO - assert something about accountManager
        });
        return d;
    }, // }}}

    function test_conversationTabs(self) { // {{{
        var d = self.setUp();
        d.addCallback(function _(irc) {
            d2 = self.callRemote('generateConversation', '#test');
            d2.addCallback(function _generatedConversation(_) {
                var testTabs = irc.nodesByAttribute('id', '#test');
                self.assertEqual(testTabs.length, 1);
                self.assertEqual(irc.activeTabId(), '#test');
            });
            return d2;
        });
        return d;
    }, // }}}

    function test_submitText(self) { // {{{
        var d = self.setUp();
        d.addCallback(function _(irc) {
            var chat = irc.getChatEntry();
            var chatentry = chat.firstNodeByAttribute('class', 'chatentry');

            chatentry.value = 'hello';
            var event = new MockEvent(chat.node);
            var d2 = chat.submit(event);
            d2.addCallback(function (_) { 
                // should reset the entry field to empty
                self.assertEqual(chatentry.value, '');

                var fgtab = irc.firstNodeByAttribute('class', 'tab');

                // the server tab should contain a span with the text
                self.assertEqual(fgtab.innerHTML.search('hello') > 0, true);
            });
            return d2;
        });
        return d;
    }, // }}}

    /* test that we can send a string without the event around it */
    function test_sendChatText(self) { // {{{
        var d = self.setUp();
        d.addCallback(function _(irc) {
            var ce = irc.getChatEntry();
            var d2 = ce.sendChatText('hello2');
            d2.addCallback(function (_) {
                var fgtab = irc.firstNodeByAttribute('class', 'tab');

                // the server tab should contain a span with the text
                self.assertEqual(fgtab.innerHTML.search('hello2') > 0, true);
            });
            return d2;
        });
        return d;
    }, // }}}

    function test_logOn(self) { // {{{
        var d = self.setUp();
        d.addCallback(function _(irc) {
            // try it with one channel
            var acctManager = irc.childWidgets[0];
            var amnode = acctManager.node;
            amnode.nick.value = 'MFen';
            amnode.channels.value = '#vellum';
            var event = new MockEvent(amnode);

            var d2 = acctManager.onLogOnSubmit(event );
            d2.addCallback(function _(response) {
                // check username/password/host are a match
                self.assertEqual(response, 
                    'connected MFen@localhost and joined #vellum');
                }
            );

            // try it with two channels
            amnode.channels.value = '#vellum,#stuff';
            var event = new MockEvent(amnode);
            var d3 = acctManager.onLogOnSubmit(event);
            d3.addCallback(function _(response) {
                // check username/password/host are a match
                self.assertEqual(response, 
                    'connected MFen@localhost and joined #vellum,#stuff');
                }
            );

            return Divmod.Defer.DeferredList([d2, d3], false, true);
            }
        );
        return d;
    }, // }}}

    /* test that getChatEntry returns a ChatEntry widget */
    function test_getChatEntry(self) { // {{{
        d = self.setUp();
        d.addCallback(function _(irc) {
            var ce = irc.getChatEntry();
            self.failUnless(ce.firstNodeByAttribute('class', 'chatentry'));
        });
        return d;
    }, // }}}

    // TODO - test keyboard login submit vs. click button submit?


    // TODO - tests for the window.location after clicking on a tab (make sure
    // there's no #fragment added by the act of clicking on the link


    function setUp(self) { // {{{
        var d = self.callRemote("newContainer");
        d.addCallback(
            function _(wi) { return self.addChildWidgetFromWidgetInfo(wi); }
            );
        return d;
    } // }}}
); // }}}

WebbyVellum.Tests.TestTopicBar = Nevow.Athena.Test.TestCase.subclass("WebbyVellum.Tests.TestTopicBar");
WebbyVellum.Tests.TestTopicBar.methods( // {{{
    function test_initialize(self) { // {{{
        d = self.setUp();
        d.addCallback(function initialize(topicbar) {
            self.assertEqual(topicbar.node.value, '');
        });
        return d;
    }, // }}}

    function test_setTopic(self) { // {{{
        d = self.setUp();
        d.addCallback(function _set(topicbar) {
            topicbar.setTopic('hello');
            self.assertEqual(topicbar.node.value, 'hello');
        });
        return d;
    }, // }}}

    function setUp(self) { // {{{
        var d = self.callRemote("newTopicBar");
        d.addCallback(
            function _(wi) { return self.addChildWidgetFromWidgetInfo(wi); }
            );
        return d;
    } // }}}
); // }}}

WebbyVellum.Tests.TestSignup = Nevow.Athena.Test.TestCase.subclass("WebbyVellum.Tests.TestSignup");
WebbyVellum.Tests.TestSignup.methods( // {{{
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
'An error occurred signing you up.  Maybe that account is already signed up.');
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

WebbyVellum.Tests.TestFileChooser = Nevow.Athena.Test.TestCase.subclass("WebbyVellum.Tests.TestFileChooser");
WebbyVellum.Tests.TestFileChooser.methods( // {{{
    function test_initialize(self) { // {{{
        var d = self.setUp();
        d.addCallback(function _(chooser) {
            /* verify that there is a New File icon present */
            var newDocumentNode = chooser.firstNodeByAttribute('vellum:name', 
                    'documentNew');
            self.assertEqual(newDocumentNode.tagName, 'table');
        });
        return d
    }, // }}}

    function test_newDocumentClick(self) { // {{{
        var d = self.setUp();
        d.addCallback(function _(chooser) {
            var ev = new MockEvent(chooser.node);
            ev.pageX = 100;
            ev.pageY = 100;

            /* verify that, initially, there is no closeUploadFrame set */
            self.failUnless(window.closeUploadFrame === undefined);

            try {
                chooser.handleNewDocument(ev);

                var iframe = Nevow.Athena.FirstNodeByAttribute(document,
                        'class', 'uploadBox');
                self.assertEqual(iframe.style['top'], '100px');
                self.assertEqual(iframe.style['left'], '100px');
                self.failUnless(iframe.src.match(/^http:\/\/.*\/upload\/$/));

                /* verify that a closeUploadFrame function has been set */
                self.failIf(window.closeUploadFrame === undefined);
            } finally {
                /* clean up the iframe, since it will never be closed */
                iframe.parentNode.removeChild(iframe);
            }
        });
        return d;
    }, // }}}

    function setUp(self) { // {{{
        var d = self.callRemote("newFileChooser");
        d.addCallback(
            function _(wi) { return self.addChildWidgetFromWidgetInfo(wi); }
            );
        return d;
    } // }}}
); // }}}

WebbyVellum.Tests.TestNameSelect = Nevow.Athena.Test.TestCase.subclass("WebbyVellum.Tests.NameSelect");
WebbyVellum.Tests.TestNameSelect.methods( // {{{
    function test_initialize(self) { // {{{
        d = self.setUp();
        d.addCallback(function initialize(nameselect) {
            self.assertEqual(nameselect.node.className, 'nameSelect');
        });
        return d;
    }, // }}}

    function test_addSetRemoveNames(self) { // {{{
        d = self.setUp();
        d.addCallback(function _set(nameselect) {
            var insert1 = ['homer', 'maggie', 'Marge', 'bart'];
            var sorted1 = ['bart', 'homer', 'maggie', 'Marge'];
            nameselect.setNames(insert1);
            /* check that all 4 are present */
            self.assertEqual(nameselect.node.options.length, 4);
            /* check that they are sorted */
            var afterInsert1 = [];
            for (var i=0; i<nameselect.node.options.length; i++)
                afterInsert1.push(nameselect.node.options[i].innerHTML);

            self.assertEqual(afterInsert1.length, sorted1.length);
            for (i=0; i<sorted1.length; i++) {
                self.assertEqual(afterInsert1[0], sorted1[0]);
            }

            /* check that capitalization is preserved */
            self.assertEqual(afterInsert1[3], 'Marge');

            nameselect.addName('lisa', {});
            /* check that lisa was inserted in alphabetical order */
            self.assertEqual(nameselect.node.options[2].innerHTML, 'lisa')

            /* remove it.. */
            nameselect.removeName('lisa');
            self.assertEqual(nameselect.node.options.length, 4);
            self.assertEqual(nameselect.node.options[2].innerHTML, 'maggie')

        });
        return d;
    }, // }}}

    function setUp(self) { // {{{
        var d = self.callRemote("newNameSelect");
        d.addCallback(
            function _(wi) { return self.addChildWidgetFromWidgetInfo(wi); }
            );
        return d;
    } // }}}
); // }}}

// vi:foldmethod=marker
