// import Nevow.Athena.Test
// import Divmod

RT = Divmod.Runtime.theRuntime;

StainedGlass.Tests.TestEnclosure = Nevow.Athena.Test.TestCase.subclass("StainedGlass.Tests.TestEnclosure");
StainedGlass.Tests.TestEnclosure.methods( // {{{
    function test_initialize(self) {  // {{{
        var d = self.setUp();
        d.addCallback(function _(enc) {
            var p = enc.node.parentNode;
            // look for an iconified widget
            var pairedIcon = RT.firstNodeByAttribute(enc.node.parentNode, 
                                                     'class',
                                                     'iconified-hidden')
            self.assertEqual(enc.iconified, pairedIcon);

            // make sure initial minimized/restored states are sane
            self.assertEqual(enc.node.className, 'enclosure decorated');
            self.assertEqual(pairedIcon.className, 'iconified-hidden');

            // make sure icon title matches main title
            var parentTitle = enc.firstNodeByAttribute(
                    'class', 'windowTitle');
            var iconTitle = RT.firstNodeByAttribute(
                    pairedIcon, 'class', 'windowTitle');
            self.assertEqual(parentTitle.innerHTML, iconTitle.innerHTML);
        });
        return d;
    }, // }}}

    function test_withArguments(self) { // {{{
        var d = self.callRemote("newEnclosure", "Foobar", "foobar");
        d.addCallback(
            function _(wi) { return self.addChildWidgetFromWidgetInfo(wi); 
        });
        d.addCallback(
            function _gotWidget(enc) {
                var parentTitle = enc.firstNodeByAttribute(
                        'class', 'windowTitle');
                self.assertEqual(parentTitle.innerHTML.search('Foobar'), 0);
                self.assertEqual(enc.node.className, 'enclosure decorated foobar');
        });
        return d;
    }, // }}}

    function test_minimizeRestore(self) { // {{{
        var d = self.setUp();
        d.addCallback(function _(enc) {
            self.assertEqual(enc.node.className, 'enclosure decorated');
            self.assertEqual(enc.iconified.className, 'iconified-hidden');
            enc.minimize();
            self.assertEqual(enc.node.className, 'enclosure-hidden decorated');
            self.assertEqual(enc.iconified.className, 'iconified');
            enc.restore();
            self.assertEqual(enc.node.className, 'enclosure decorated');
            self.assertEqual(enc.iconified.className, 'iconified-hidden');
        });
        return d;
    }, // }}}

    function setUp(self) { // {{{
        var d = self.callRemote("newEnclosure");
        d.addCallback(
            function _(wi) { return self.addChildWidgetFromWidgetInfo(wi); }
            );
        return d;
    } // }}}
); // }}}

StainedGlass.Tests.TestTextArea = Nevow.Athena.Test.TestCase.subclass("StainedGlass.Tests.TestTextArea");
StainedGlass.Tests.TestTextArea.methods( // {{{
    function test_initialContent(self) { // {{{
        var d = self.callRemote("newTextArea", 
            '<div xmlns="' + XHTMLNS + '"><b>Content</b></div>');
        d.addCallback(
            function _(wi) { return self.addChildWidgetFromWidgetInfo(wi); }
            );
        d.addCallback(
            function _(ta) {
                self.assertEqual(ta.node.innerHTML.search('<b>Content</b>'), 42);
                }
            );
        return d;
    }, // }}}

    function test_appendTo(self) { // {{{
        var d = self.setUp();
        d.addCallback(
            function _(ta) {
                var n = ta.node;
                self.assertEqual(n.innerHTML.length, 0);
                ta.appendTo('<span xmlns="' + XHTMLNS + '">Babar</span>');
                self.failUnless(n.innerHTML.search('Babar') >= 0);
                ta.appendTo('<p xmlns="' + XHTMLNS + '">Hi</p>');
                self.failUnless(n.innerHTML.search('Hi</p>') >= 0);
            });
        return d;
    }, // }}}

    function setUp(self) { // {{{
        var d = self.callRemote("newTextArea");
        d.addCallback(
            function _(wi) { return self.addChildWidgetFromWidgetInfo(wi); }
            );
        return d;
    } // }}}
); // }}}

// vi:foldmethod=marker
