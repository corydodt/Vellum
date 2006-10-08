// import Nevow.Athena.Test
// import Divmod

RT = Divmod.Runtime.theRuntime;

Windowing.Tests.TestEnclosure = Nevow.Athena.Test.TestCase.subclass("Windowing.Tests.TestEnclosure");
Windowing.Tests.TestEnclosure.methods( // {{{
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
            self.assertEqual(enc.node.className, 'enclosure');
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
                self.assertEqual(enc.node.className, 'enclosure foobar');
        });
        return d;
    }, // }}}

    function test_minimizeRestore(self) { // {{{
        var d = self.setUp();
        d.addCallback(function _(enc) {
            self.assertEqual(enc.node.className, 'enclosure');
            self.assertEqual(enc.iconified.className, 'iconified-hidden');
            enc.minimize();
            self.assertEqual(enc.node.className, 'enclosure-hidden');
            self.assertEqual(enc.iconified.className, 'iconified');
            enc.restore();
            self.assertEqual(enc.node.className, 'enclosure');
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

// vi:foldmethod=marker
