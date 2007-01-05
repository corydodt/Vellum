// import Nevow.Athena.Test
// import Divmod

MockEvent = Divmod.Class.subclass('MockEvent');
MockEvent.methods( // {{{
    function __init__(self, node) { self.target = self.srcElement = node; },

    function stopPropagation(self) { /* */ },

    function preventDefault(self) { /* */ }
); // }}}

MockChatEntry = Divmod.Class.subclass('MockChatEntry');
MockChatEntry.methods( // {{{
    function sendChatText(self, message) { // {{{
        self.message = message;
    } // }}}
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

            var fgtab = irc.firstNodeByAttribute('class', 'tab');

            // the server tab should be in the foreground
            self.assertEqual(fgtab.id, '**SERVER**');

            // the nick field should not be populated.
            self.assertEqual(accountManager.node.nick.value, '');

            // TODO - assert something about accountManager
        });
        return d;
    }, // }}}

    /* test that the server can send us a conversation pane */
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

WebbyVellum.Tests.TestChatEntry = Nevow.Athena.Test.TestCase.subclass("WebbyVellum.Tests.TestChatEntry");
WebbyVellum.Tests.TestChatEntry.methods( // {{{
    function test_initialize(self) { // {{{
        var d = self.setUp();
        d.addCallback(function gotChatEntry(chatentry) {
            self.assertEqual(chatentry.node.chatentry.value, '');
        });
        return d;
    }, // }}}

    /* test that we can send a string without the event around it */
    function test_sendChatText(self) { // {{{
        var d = self.setUp();
        d.addCallback(function _(chatentry) {
            var d2 = chatentry.sendChatText('hello2');
            d2.addCallback(function gotResponse(value) {
                self.assertEqual(value, 'ok');
            });
            return d2;
        });
        return d;
    }, // }}}

    /* test that we can use an event to send the string */
    function test_submitText(self) { // {{{
        var d = self.setUp();
        d.addCallback(function _(chatentry) {
            var input = chatentry.node.chatentry;

            input.value = 'hello';
            var event = new MockEvent(input);
            var d2 = chatentry.submit(event);
            d2.addCallback(function gotResponse(value) {
                self.assertEqual(value, 'ok');
            });
            return d2;
        });
        return d;
    }, // }}}

    function setUp(self) { // {{{
        var d = self.callRemote("newChatEntry");
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

WebbyVellum.Tests.TestAccountManager = Nevow.Athena.Test.TestCase.subclass("WebbyVellum.Tests.TestAccountManager");
WebbyVellum.Tests.TestAccountManager.methods( // {{{
    function test_initialize(self) { // {{{
        var d = self.setUp();
        d.addCallback(function gotAccountManager(am) {
            // the nick field should not be populated.
            self.assertEqual(am.node.nick.value, '');
            var d2 = self.setUp({'nick':'woot'});
            d2.addCallback(function gotAccountManager2(am2) {
                // the nick field *should* be populated.
                self.assertEqual(am2.node.nick.value, 'woot');
                // check autoHide
                self.assertEqual(am2.node.style['display'], 'none');
            });
            return d2;
        });
        return d;
    }, // }}}

    function test_logOn(self) { // {{{
        var d = self.setUp();
        d.addCallback(function gotAccountManager(acctManager) {
            // try it with one channel
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
            d2.addCallback(function finishedTest1(ignored) { // {{{
                amnode.channels.value = '#vellum,#stuff';
                var event = new MockEvent(amnode);
                var d3 = acctManager.onLogOnSubmit(event);
                d3.addCallback(function finishedSubmit(response) {
                    // check username/password/host are a match
                    self.assertEqual(response, 
                        'connected MFen@localhost and joined #vellum,#stuff');
                    }
                );
                return d3;
            }); // }}}

            return d2;
        });
        return d;
    }, // }}}

    function setUp(self, config) { // {{{
        if (config === undefined) config = {};

        nickArg = (config.nick || null);
        autoHideArg = (config.autoHide || null);

        d = self.callRemote("newAccountManager", nickArg);
        d.addCallback(function gotAccountManager(aminfo) {
            return self.addChildWidgetFromWidgetInfo(aminfo);
        });
        return d;
    } // }}}
); // }}}
 
WebbyVellum.Tests.TestFileChooser = Nevow.Athena.Test.TestCase.subclass("WebbyVellum.Tests.TestFileChooser");
WebbyVellum.Tests.TestFileChooser.methods( // {{{
    function test_initialize(self) { // {{{
        var d = self.setUp();
        d.addCallback(function _(chooser) {
            /* verify that there is a New File icon present */
            var newDocumentNode = chooser.firstNodeByClass('documentNew');
            self.assertEqual(newDocumentNode.tagName, 'table');
        });
        return d
    }, // }}}

    function test_initializeWithIcons(self) { // {{{
        var d = self.setUp(['b','a','c']);
        d.addCallback(function _(chooser) {
            /* verify that the chooser begins in sorted order */
            var sorted1 = ['a','b','c'];
            _items = chooser._iconsByLabel();
            
            self.assertEqual(_items.length, sorted1.length);
            for (i=0; i<sorted1.length; i++) {
                self.assertEqual(_items[i][0], sorted1[i]);
            }
            return null;
        });
        return d;
    }, // }}}

    function test_addIcon(self) { // {{{
        var d = self.setUp(['b','a','c']);
        d.addCallback(function _(chooser) {
            var d2 = self.callRemote("addNewIcon", "ax");
            d2.addCallback(function _(ignored) {
                /* verify that the chooser sorts the icon in */
                var sorted1 = ['a', 'ax', 'b', 'c'];
                
                var labels = chooser.nodesByClass('chooserIconLabel');
                self.assertEqual(labels.length, sorted1.length);
                for (var i=0; i<sorted1.length; i++) {
                    self.assertEqual(labels[i].innerHTML, sorted1[i]);
                }
                return null;
            });
            return d2;
        });
        return d;
    }, // }}}

    function test_newDocumentClick(self) { // {{{
        var d = self.setUp();
        d.addCallback(function _(chooser) {
            var ev = new MockEvent(chooser.node);
            ev.pageX = 100;
            ev.pageY = 100;

            /* verify that, initially, there is no closeUploadFrame set */
            self.failUnless(window.closeUploadFrame === null);

            try {
                chooser.handleNewDocument(ev);

                var iframe = Nevow.Athena.FirstNodeByAttribute(document,
                        'class', 'uploadBox');
                self.assertEqual(iframe.style['top'], '100px');
                self.assertEqual(iframe.style['left'], '100px');
                self.failUnless(iframe.src.match(/^http:\/\/.*\/upload\/$/));

                /* verify that a closeUploadFrame function has been set */
                self.failIf(window.closeUploadFrame === undefined);

                /* verify that nothing happens if you click twice */
                var currentCloser = window.closeUploadFrame;
                chooser.handleNewDocument(ev);
                self.failUnless(window.closeUploadFrame === currentCloser);
                self.failUnless(iframe ===
                        Nevow.Athena.FirstNodeByAttribute(document, 'class',
                        'uploadBox'));
            } finally {
                /* clean up the iframe, since it will never be closed */
                iframe.parentNode.removeChild(iframe);
            }
        });
        return d;
    }, // }}}

    function setUp(self, /* optional */ labels) { // {{{
        if (labels !== undefined) {
            var d = self.callRemote("newFileChooser", labels);
        } else {
            var d = self.callRemote("newFileChooser");
        }
        d.addCallback(
            function _(wi) { return self.addChildWidgetFromWidgetInfo(wi); });
        return d;
    } // }}}
); // }}}

WebbyVellum.Tests.TestNameSelect = Nevow.Athena.Test.TestCase.subclass("WebbyVellum.Tests.TestNameSelect");
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
                self.assertEqual(afterInsert1[i], sorted1[i]);
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

WebbyVellum.Tests.TestConversationEnclosure = Nevow.Athena.Test.TestCase.subclass("WebbyVellum.Tests.TestConversationEnclosure");
WebbyVellum.Tests.TestConversationEnclosure.methods( // {{{
    function test_initialize(self) { // {{{
        var d = self.setUp();
        d.addCallback(function gotEnclosure(enclosure) {
            self.failUnless(enclosure.conversationName == '#foo');
        });
        return d;
    }, // }}}

    function test_getChatEntry(self) { // {{{
        var d = self.setUp();
        d.addCallback(function gotEnclosure(enclosure) {
            self.assertThrows(Divmod.Runtime.NodeAttributeError,
                function () { enclosure.getChatEntry() });
            enclosure.chatentry = 'fake';
            self.assertEqual(enclosure.getChatEntry(), 'fake');
            enclosure.chatentry = null;
            var chatNode = document.createElement('div');
            chatNode.setAttribute('class', 'chatentry');
            self.node.appendChild(enclosure.node);
            enclosure.node.appendChild(chatNode);
            /* we are not actually going to get a chatentry back,
             * since we never created one.  Just check for enclosure,
             * which is the nearest enclosing widget to the chatentry node
             */
            self.assertEqual(enclosure.getChatEntry(), enclosure);
        });
        return d;
    }, // }}}

    function test_obscureAllRevealAll(self) { // {{{
        var d = self.setUp();
        d.addCallback(function gotEnclosure(enclosure) {
            enclosure.chatentry = new MockChatEntry();
            var ev = new MockEvent(enclosure.node);
            enclosure.onRevealAllClicked(ev);
            self.assertEqual(enclosure.chatentry.message, "/REVEALALL #foo");
            enclosure.onObscureAllClicked(ev);
            self.assertEqual(enclosure.chatentry.message, "/OBSCUREALL #foo");
        });
        return d;
    }, // }}}

    function setUp(self) { // {{{
        var d = self.callRemote("newConversationEnclosure");
        d.addCallback(function gotEnclosure(enclosureInfo) {
            var d2 = self.addChildWidgetFromWidgetInfo(enclosureInfo);
            d2.addCallback(function gotEnclosure(enclosure) {
                return enclosure;
            });
            return d2;
        });
        return d;
    } // }}}
); // }}}

// vi:foldmethod=marker
