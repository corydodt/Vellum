// import Nevow.Athena.Test
// import Divmod.Runtime

XHTMLNS = "http://www.w3.org/1999/xhtml";

RT = Divmod.Runtime.theRuntime;

Tabby.Tests.TestTabs = Nevow.Athena.Test.TestCase.subclass("Tabby.Tests.TestTabs");
Tabby.Tests.TestTabs.methods( // {{{
    function test_initialTabId(self) { // {{{
        var d = self.callRemote("newTabWidget", 'woop', 'Woop');
        d.addCallback(
            function(wi) { return self.addChildWidgetFromWidgetInfo(wi); }
            );
        d.addCallback(
            function(tabs) { 
                self.assertEqual(tabs.activeTabId(), 'woop'); 
                self.assertEqual(
                        tabs.getHandleForId('woop').innerHTML, 'Woop'); 
                }
            );
        return d;
    }, // }}}

    function test_initialTabIdAndContent(self) { // {{{
        var d = self.callRemote("newTabWidget", 'woop', 'Woop', 
            '<div xmlns="' + XHTMLNS + '"><b>Content</b></div>');
        d.addCallback(
            function _(wi) { return self.addChildWidgetFromWidgetInfo(wi); }
            );
        d.addCallback(
            function _(tabs) {
                var pane = tabs.getPaneForId('woop');
                self.assertEqual(pane.innerHTML.search('<b>Content</b>'), 42);
                }
            );
        return d;
    }, // }}}

    function test_clicked(self) { // {{{
        var d = self.setUp();
        d.addCallback(
            function _(tabs) { 
                tabs.addTab('1', 'One');
                tabs.addTab('2', 'Two');
                self.assertEqual(tabs.activeTabId(), '2');
                var onehandle = RT.firstNodeByAttribute(tabs.node, 'href', '#1');
                tabs.clicked(onehandle);
                self.assertEqual(tabs.activeTabId(), '1');
            });
    }, // }}}

    function test_show(self) { // {{{
        var d = self.setUp();
        d.addCallback(
            function _(tabs) { 
                tabs.addTab('1', 'One');
                tabs.addTab('2', 'Two');
                self.assertEqual(tabs.activeTabId(), '2');
                tabs.show('1');
                self.assertEqual(tabs.activeTabId(), '1');
                }
            );
        return d;
    }, // }}}

    function test_removeTab(self) { // {{{
        var d = self.setUp();
        d.addCallback(
            function _(tabs) {
                tabs.addTab('1', 'One');
                tabs.addTab('2', 'Two');
                var handleNode = RT.firstNodeByAttribute(
                        tabs.node, 'class', 'handles');
                var paneNode = RT.firstNodeByAttribute(
                        tabs.node, 'class', 'panes');
                self.assertEqual(handleNode.childNodes.length, 2);
                self.assertEqual(paneNode.childNodes.length, 2);
                tabs.removeTab('1');
                self.assertEqual(handleNode.childNodes.length, 1);
                self.assertEqual(paneNode.childNodes.length, 1);
                self.assertThrows(
                        Divmod.Runtime.NodeAttributeError,
                        function _() { tabs.show('1'); }
                        );
            });
        return d;
    }, // }}}

    function test_appendToTab(self) { // {{{
        var d = self.setUp();
        d.addCallback(
            function _(tabs) {
                tabs.addTab('1', 'One');
                var p = tabs.getPaneForId('1');
                self.assertEqual(p.innerHTML.length, 0);
                tabs.appendToTab('1', '<span xmlns="' + XHTMLNS + '">Babar</span>');
                self.failUnless(p.innerHTML.search('Babar') >= 0);
                tabs.appendToTab('1', '<p xmlns="' + XHTMLNS + '">Hi</p>');
                self.failUnless(p.innerHTML.search('Hi</p>') >= 0);
            });
        return d;
    }, // }}}

    function setUp(self) { // {{{
        var d = self.callRemote("newTabWidget");
        d.addCallback(
            function _(wi) { return self.addChildWidgetFromWidgetInfo(wi); }
            );
        return d;
    } // }}}
); // }}}

// vi:foldmethod=marker
