// import Nevow.Athena.Test
// import Divmod

MockEvent = Divmod.Class.subclass('MockEvent');
MockEvent.methods(
    function __init__(self, node) { self.target = self.srcElement = node; },

    function stopPropagation(self) { /* */ },

    function preventDefault(self) { /* */ }
);


WebbyVellum.Tests.TestIRCContainer = Nevow.Athena.Test.TestCase.subclass("WebbyVellum.Tests.TestIRCContainer");
WebbyVellum.Tests.TestIRCContainer.methods(
    function test_initialize(self) {
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

            // TODO - assert something about accountManager
        });
    },

    function test_conversationTabs(self) {
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
    },

    function test_submitText(self) {
        var d = self.setUp();
        d.addCallback(function _(irc) {
            var chat = irc.childWidgets[2];
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
    },

    function test_logOn(self) {
        var d = self.setUp();
        d.addCallback(function _(irc) {
            // try it with one channel
            var acctManager = irc.childWidgets[0];
            var amnode = acctManager.node;
            amnode.username.value = 'MFen';
            amnode.password.value = 'ninjas';
            amnode.channels.value = '#vellum';
            var event = new MockEvent(amnode);

            var d2 = acctManager.onLogOnSubmit(event );
            d2.addCallback(function _(response) {
                // check username/password/host are a match
                self.assertEqual(response, 
                    'connected MFen:ninjas@localhost and joined #vellum');
                }
            );

            // try it with two channels
            amnode.channels.value = '#vellum,#stuff';
            var event = new MockEvent(amnode);
            var d3 = acctManager.onLogOnSubmit(event);
            d3.addCallback(function _(response) {
                // check username/password/host are a match
                self.assertEqual(response, 
                    'connected MFen:ninjas@localhost and joined #vellum,#stuff');
                }
            );

            return Divmod.Defer.DeferredList([d2, d3], false, true);
            }
        );
        return d;
    },


    // TODO - test keyboard login submit vs. click button submit?


    // TODO - tests for the window.location after clicking on a tab (make sure
    // there's no #fragment added by the act of clicking on the link


    function setUp(self) {
        var d = self.callRemote("newContainer");
        d.addCallback(
            function _(wi) { return self.addChildWidgetFromWidgetInfo(wi); }
            );
        return d;
    }
);
